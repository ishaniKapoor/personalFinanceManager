import io
import base64
from flask import Flask, render_template, request, redirect, url_for, flash, Response
import matplotlib.pyplot as plt
from db import queries

app = Flask(__name__)
app.secret_key = "supersecret"  # in production use env var


@app.route("/")
def index():
    txs = queries.list_transactions(limit=20)
    return render_template("index.html", transactions=txs)


@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        type_ = request.form["type"]
        category = request.form["category"] or None
        amount = request.form["amount"]
        date_iso = request.form["date"]
        notes = request.form.get("notes")
        queries.add_transaction(
            type_=type_,
            category=category,
            amount_dollars=amount,
            date_iso=date_iso,
            notes=notes,
        )
        flash("Transaction added!")
        return redirect(url_for("index"))
    return render_template("add.html")


@app.route("/summary/<int:year>/<int:month>")
def summary(year, month):
    totals = queries.monthly_income_expense(1, year, month)
    breakdown = queries.category_breakdown(
        1, f"{year}-{month:02d}-01", f"{year}-{month:02d}-31"
    )

    # daily expenses for line chart
    txs = queries.list_transactions(
        user_id=1,
        start_date=f"{year}-{month:02d}-01",
        end_date=f"{year}-{month:02d}-31",
        type_="expense",
        limit=1000,
    )
    daily_totals = {}
    for tx in txs:
        day = tx["date"]
        amt = tx["amount_cents"] / 100
        daily_totals[day] = daily_totals.get(day, 0) + amt

    days = sorted(daily_totals.keys())
    amounts = [daily_totals[d] for d in days]

    return render_template(
        "summary.html",
        totals=totals,
        breakdown=breakdown,
        year=year,
        month=month,
        days=days,
        amounts=amounts,
    )


# ---------- CHART HELPERS ----------

def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)  # free memory
    return encoded


@app.route("/chart/pie/<int:year>/<int:month>")
def chart_pie(year, month):
    breakdown = queries.category_breakdown(
        1, f"{year}-{month:02d}-01", f"{year}-{month:02d}-31"
    )
    labels = [cat for cat, _ in breakdown]
    sizes = [float(amount) for _, amount in breakdown]

if __name__ == "__main__":
    app.run(debug=True)