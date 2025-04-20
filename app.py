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
    <form method="POST" action="/submit" enctype="multipart/form-data">
        <label>Email:</label><input type="email" name="email" required><br>
        <label>Customer Name:</label><input type="text" name="customer" required><br>
        <label>Customer Phone (optional):</label><input type="text" name="phone"><br>
        <label>Date:</label><input type="date" name="date"><br>
        <label>Tax (%):</label><input type="number" name="tax" step="0.01"><br>
        <label>Discount ($):</label><input type="number" name="discount" step="0.01"><br><br>

        {% for i in range(1, 5) %}
        <div class="item-row">
            <strong>Item {{ i }}</strong><br>
            <label>Description:</label><input type="text" name="desc{{ i }}"><br>
            <label>Quantity:</label><input type="number" name="qty{{ i }}"><br>
            <label>Rate ($):</label><input type="number" name="rate{{ i }}" step="0.01"><br>
        </div>
        {% endfor %}

        <label>Business Name:</label><input type="text" name="biz_name"><br>
        <label>Business Address:</label><textarea name="biz_address"></textarea><br>
        <label>Business Phone:</label><input type="text" name="biz_phone"><br>
        <label>Business Email:</label><input type="email" name="biz_email"><br>
        <label>Business Website:</label><input type="text" name="biz_website"><br><br>

        <label>Custom Header Title:</label><input type="text" name="custom_title"><br>
        <label>Footer Note:</label><textarea name="footer_note"></textarea><br>
        <label>Upload Logo (optional):</label><input type="file" name="logo"><br>
        <input type="checkbox" name="show_phone"> Include phone number<br>
        <input type="checkbox" name="show_signature" checked> Include signature<br>
        <input type="checkbox" name="show_thanks" checked> Show "Thank You" message<br><br>

        <label>Type Your Name for Signature:</label><input type="text" name="typed_signature"><br><br>

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
    phone = request.form.get("phone")
    show_phone = request.form.get("show_phone")
    show_signature = request.form.get("show_signature")
    show_thanks = request.form.get("show_thanks")
    footer_note = request.form.get("footer_note")
    custom_title = request.form.get("custom_title") or "Estimate"
    typed_signature = request.form.get("typed_signature")

    biz_name = request.form.get("biz_name")
    biz_address = request.form.get("biz_address")
    biz_phone = request.form.get("biz_phone")
    biz_email = request.form.get("biz_email")
    biz_website = request.form.get("biz_website")

    date = request.form.get("date") or datetime.now().strftime("%Y-%m-%d")
    estimate_id = str(uuid.uuid4())[:8]
    tax_rate = float(request.form.get("tax") or 0) / 100
    discount = float(request.form.get("discount") or 0)

    items = []
    total = 0
    for i in range(1, 5):
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

    logo = request.files.get("logo")
    if logo and logo.filename:
        logo_path = f"{PDF_DIR}/logo_{estimate_id}.png"
        logo.save(logo_path)
        try:
            pdf.image(logo_path, x=80, w=50)
        except:
            pass

    if biz_name:
        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(200, 10, txt=biz_name, ln=True)
    pdf.set_font("Arial", size=10)
    if biz_address:
        pdf.multi_cell(0, 8, txt=biz_address)
    if biz_phone:
        pdf.cell(200, 8, txt=f"Phone: {biz_phone}", ln=True)
    if biz_email:
        pdf.cell(200, 8, txt=f"Email: {biz_email}", ln=True)
    if biz_website:
        pdf.cell(200, 8, txt=f"Website: {biz_website}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", style='', size=12)
    pdf.cell(200, 10, txt=f"{custom_title} #{estimate_id}", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Customer: {customer}", ln=True)
    pdf.cell(200, 10, txt=f"Date: {date}", ln=True)
    if show_phone and phone:
        pdf.cell(200, 10, txt=f"Phone: {phone}", ln=True)
    pdf.ln(10)

    for item in items:
        pdf.cell(200, 10, txt=f"{item[0]} - Qty: {item[1]} @ ${item[2]} = ${item[3]:.2f}", ln=True)

    pdf.ln(5)
    pdf.cell(200, 10, txt=f"Subtotal: ${total:.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Tax: ${tax_amount:.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Discount: -${discount:.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Grand Total: ${grand_total:.2f}", ln=True)

    if footer_note:
        pdf.ln(10)
        pdf.multi_cell(0, 10, txt=f"Note: {footer_note}")

    if show_signature and typed_signature:
        pdf.ln(15)
        pdf.set_font("Arial", style='I', size=16)
        pdf.cell(200, 10, txt=f"Signed: {typed_signature}", ln=True)

    if show_thanks:
        pdf.ln(10)
        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(200, 10, txt="Thank you for your business!", ln=True, align='C')

    pdf.output(filename)
    return send_file(filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
