from flask import Flask, request, send_file, render_template_string, redirect, url_for
from fpdf import FPDF
import os
from datetime import datetime
import uuid

app = Flask(__name__)

PDF_DIR = "pdfs"
os.makedirs(PDF_DIR, exist_ok=True)

FORM_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>QuickQuote AI</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        input, textarea { width: 100%; padding: 8px; margin: 5px 0; }
        .item-row { border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; }
    </style>
</head>
<body>
    <h1>QuickQuote AI - Estimate Generator</h1>
    <form method="POST" action="/submit">
        <label>Email:</label><input type="email" name="email" required><br>
        <label>Customer Name:</label><input type="text" name="customer" required><br>
        <label>Date:</label><input type="date" name="date"><br>
        <label>Tax (%):</label><input type="number" name="tax" step="0.01"><br>
        <label>Discount ($):</label><input type="number" name="discount" step="0.01"><br><br>

        {% for i in range(1, 11) %}
        <div class="item-row">
            <strong>Item {{ i }}</strong><br>
            <label>Description:</label><input type="text" name="desc{{ i }}"><br>
            <label>Quantity:</label><input type="number" name="qty{{ i }}"><br>
            <label>Rate ($):</label><input type="number" name="rate{{ i }}" step="0.01"><br>
        </div>
        {% endfor %}

        <input type="submit" value="Generate Estimate">
    </form>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(FORM_HTML)

@app.route("/submit", methods=["POST"])
def submit():
    customer = request.form.get("customer")
    date = request.form.get("date") or datetime.now().strftime("%Y-%m-%d")
    estimate_id = str(uuid.uuid4())[:8]
    tax_rate = float(request.form.get("tax") or 0) / 100
    discount = float(request.form.get("discount") or 0)

    items = []
    total = 0
    for i in range(1, 11):
        desc = request.form.get(f"desc{i}")
        qty = request.form.get(f"qty{i}")
        rate = request.form.get(f"rate{i}")
        if desc and qty and rate:
            qty = int(qty)
            rate = float(rate)
            line_total = qty * rate
            total += line_total
            items.append((desc, qty, rate, line_total))

    tax_amount = total * tax_rate
    grand_total = total + tax_amount - discount

    filename = f"{PDF_DIR}/{estimate_id}.pdf"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Estimate #{estimate_id}", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Customer: {customer}", ln=True)
    pdf.cell(200, 10, txt=f"Date: {date}", ln=True)
    pdf.ln(10)

    for item in items:
        pdf.cell(200, 10, txt=f"{item[0]} - Qty: {item[1]} @ ${item[2]} = ${item[3]:.2f}", ln=True)

    pdf.ln(5)
    pdf.cell(200, 10, txt=f"Subtotal: ${total:.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Tax: ${tax_amount:.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Discount: -${discount:.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Grand Total: ${grand_total:.2f}", ln=True)

    pdf.output(filename)
    return send_file(filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
