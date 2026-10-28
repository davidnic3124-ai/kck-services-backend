from datetime import date

def count_rental_days(start_date: date, end_date: date) -> int:
    # Same-day return counts as 1 day; otherwise the number of nights
    return max((end_date - start_date).days, 1)

def service_cost(price: float, unit: str, days: int) -> float:
    if unit == "per_day":
        return price * days
    if unit == "per_month":
        return price * max(round(days / 30), 1)
    if unit == "per_hour":
        return price * 8 * days  # assume an 8-hour working day
    return price  # per_trip: charged once

def calculate_quote(daily_rate: float, days: int, svc_price: float, svc_unit: str | None, discount_percent: int) -> dict:
    car_cost = round(daily_rate * days, 2)
    extra = round(service_cost(svc_price, svc_unit, days), 2) if svc_unit else 0.0
    subtotal = round(car_cost + extra, 2)
    discount_amount = round(subtotal * discount_percent / 100, 2)
    return {
        "rental_days": days,
        "car_cost": car_cost,
        "service_cost": extra,
        "subtotal": subtotal,
        "discount_percent": discount_percent,
        "discount_amount": discount_amount,
        "total_price": round(subtotal - discount_amount, 2),
    }
