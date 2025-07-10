from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, schemas, database
from fpdf import FPDF
from fastapi.responses import StreamingResponse
import io
import os
from dotenv import load_dotenv
import google.generativeai as genai

# ✅ Explicitly load .env from backend directory
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY not found in .env")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash")

# ✅ Create DB tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# ✅ CORS for React frontend on port 3001
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ DB dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/expenses", response_model=list[schemas.Expense])
def read_expenses(db: Session = Depends(get_db)):
    return db.query(models.Expense).all()

@app.post("/expenses", response_model=schemas.Expense)
def create_expense(expense: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    # ✅ Fixed: Use model_dump() instead of dict()
    db_expense = models.Expense(**expense.model_dump())
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense

@app.put("/expenses/{expense_id}", response_model=schemas.Expense)
def update_expense(expense_id: int, updated: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    # ✅ Fixed: Use model_dump() instead of dict() for Pydantic v2 compatibility
    for key, value in updated.model_dump().items():
        setattr(expense, key, value)
    
    db.commit()
    db.refresh(expense)
    return expense

@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(expense)
    db.commit()
    return {"message": "Deleted successfully"}

@app.get("/expenses/pdf")
def generate_pdf(db: Session = Depends(get_db)):
    try:
        expenses = db.query(models.Expense).all()

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Expense Summary", ln=True, align='C')

        if not expenses:
            pdf.cell(200, 10, txt="No expenses found.", ln=True)
        else:
            # ✅ Prepare Gemini prompt without ₹
            prompt = "Summarize this expense list in a simple line like 'You spent the most on groceries. The total expense is Rs.3,200 across 12 items.'\n\n"
            for exp in expenses:
                prompt += f"- {exp.title}, Rs.{exp.amount}, {exp.category}, {exp.date}\n"

            # ✅ Call Gemini
            response = model.generate_content(prompt)
            summary = response.text.strip().replace("₹", "Rs.")

            # ✅ Write to PDF
            pdf.multi_cell(0, 10, txt=summary)
            pdf.ln(5)
            pdf.cell(200, 10, txt="Expense Details:", ln=True)

            for exp in expenses:
                line = f"{exp.title} - Rs.{exp.amount} on {exp.date}"
                pdf.cell(200, 10, txt=line, ln=True)

        pdf_bytes = pdf.output(dest="S").encode("latin1")

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=expense_summary.pdf"}
        )

    except Exception as e:
        print("PDF generation failed:", e)
        raise HTTPException(status_code=500, detail="Failed to generate PDF")