from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import shutil
import pytesseract
import os
from PIL import Image, ImageOps, ImageEnhance
import re

from database import create_database, save_bill, get_bills, add_expense, clear_bills
from ml_model import detect_anomalies


if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"


os.makedirs("uploads", exist_ok=True)

app = FastAPI()

create_database()


@app.get("/", response_class=HTMLResponse)
def home():

    with open("templates/index.html", "r", encoding="utf-8") as file:
        return file.read()


def extract_bill_details(text):

    details = {}

    text = text.replace("\r", "\n")

    lines = text.split("\n")

    bill_number = None
    bill_date = None
    amount = None

    for line in lines:

        line = line.strip()

        if not line:
            continue

        number = re.search(
            r"(?:invoice|bill|receipt|reference)"
            r"\s*(?:no|number|#)?"
            r"\s*[:.-]?\s*([A-Z0-9]+(?:[-/][A-Z0-9]+)*)",
            line,
            re.IGNORECASE
        )

        if number and not bill_number:

            value = number.group(1)

            if value.lower() not in [
                "no",
                "number",
                "date"
            ]:
                bill_number = value


        date = re.search(
            r"\b\d{1,2}\s*[-/.]\s*"
            r"(?:\d{1,2}|[A-Za-z]{3,9})"
            r"\s*[-/.]\s*\d{2,4}\b",
            line
        )

        if date and not bill_date:
            bill_date = date.group(0)


        date2 = re.search(
            r"\b\d{1,2}\s+\w+\s+\d{4}\b",
            line
        )

        if date2 and not bill_date:
            bill_date = date2.group(0)


    total_words = [
        "total",
        "grand total",
        "amount due",
        "balance due",
        "net amount",
        "total amount",
        "payable",
        "amount payable"
    ]

    for line in lines:

        lower_line = line.lower()

        for word in total_words:

            if word in lower_line:

                numbers = re.findall(
                    r"(?:₹|rs\.?|inr)?\s*"
                    r"\d[\d,]*(?:\.\d{1,2})?",
                    line,
                    re.IGNORECASE
                )

                if numbers:

                    value = numbers[-1]

                    value = re.sub(
                        r"[^0-9.]",
                        "",
                        value
                    )

                    if value:
                        amount = value
                        break

        if amount:
            break


    if not amount:

        currency_numbers = re.findall(
            r"(?:₹|rs\.?|inr)\s*"
            r"\d[\d,]*(?:\.\d{1,2})?",
            text,
            re.IGNORECASE
        )

        if currency_numbers:

            values = []

            for value in currency_numbers:

                value = re.sub(
                    r"[^0-9.]",
                    "",
                    value
                )

                if value:
                    values.append(float(value))

            if values:
                amount = str(max(values))


    if not amount:

        numbers = re.findall(
            r"\b\d[\d,]*\.\d{2}\b",
            text
        )

        if numbers:

            values = []

            for value in numbers:

                value = value.replace(",", "")

                try:
                    values.append(float(value))
                except:
                    pass

            if values:
                amount = str(max(values))


    if bill_number:
        details["bill_number"] = bill_number

    if bill_date:
        details["bill_date"] = bill_date

    if amount:
        details["total_amount"] = amount

    return details


@app.post("/upload-file/")
def upload_file(file: UploadFile = File(...)):

    file_path = "uploads/" + file.filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    image = Image.open(file_path)

    text = pytesseract.image_to_string(
        image,
        config="--psm 6"
    )

    details = extract_bill_details(text)

    if len(details) < 3:

        gray = ImageOps.grayscale(image)

        gray = ImageEnhance.Contrast(gray).enhance(2)

        text = pytesseract.image_to_string(
            gray,
            config="--psm 11"
        )

        new_details = extract_bill_details(text)

        for key in new_details:

            if key not in details:
                details[key] = new_details[key]


    save_bill(
        file.filename,
        details.get("bill_number"),
        details.get("bill_date"),
        details.get("total_amount")
    )

    return RedirectResponse(
        url="/",
        status_code=303
    )


@app.get("/bills")
def get_all_bills():

    bills = get_bills()

    return {
        "bills": bills
    }


@app.post("/add-expense/")
def add_new_expense(
    amount: float = Form(...)
):

    add_expense(amount)

    return RedirectResponse(
        url="/",
        status_code=303
    )


@app.get("/anomalies")
def get_anomalies():

    data = detect_anomalies()

    return data.to_dict(
        orient="records"
    )

@app.post("/clear-data/")
def clear_data():

    clear_bills()

    return RedirectResponse(
        url="/",
        status_code=303
    )