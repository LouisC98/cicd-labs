"""Tests unitaires des règles de prix — POINT DE DÉPART (Atelier 1).

Complétez ce fichier : objectif >= 90 % de couverture sur minishop/pricing.py.
"""

from decimal import Decimal

import pytest

from minishop.pricing import coupon_discount, line_total, money, quote, shipping_cost

pytestmark = pytest.mark.unit


def test_money_arrondi_commercial():
    """0.125 s'arrondit à 0.13 (ROUND_HALF_UP), pas 0.12."""
    assert money("0.125") == Decimal("0.13")


def test_line_total_sans_remise():
    assert line_total(Decimal("12.50"), 2) == Decimal("25.00")

def test_line_total_remise_volume_a_10():
    assert line_total(Decimal("10"), 10) == Decimal("95.00")

def test_line_total_pas_de_remise_volume_a_9():
    assert line_total(Decimal("10"), 9) == Decimal("90.00")

@pytest.mark.parametrize("qty", [0, -1, 100, "2", True])
def test_quantite_invalide(qty):
    with pytest.raises(ValueError):
        line_total(Decimal("10"), qty)

def test_quote_panier_vide():
    """Un panier vide coûte 0 € : pas de frais de livraison."""
    q = quote([])
    assert q.total == Decimal("0.00")
    assert q.shipping == Decimal("0.00")

@pytest.mark.parametrize("coupon, subtotal, attendu", [
    ("WELCOME10", Decimal("19.99"), Decimal("0.00")),
    ("WELCOME10", Decimal("20.00"), Decimal("2.00")),
    ("FIXED5", Decimal("29.99"), Decimal("0.00")),
    ("FIXED5", Decimal("30.00"), Decimal("5.00")),
    ("", Decimal("30.00"), Decimal("0.00")),
    ("welcome10", Decimal("20.00"), Decimal("2.00")),
])
def test_coupon_discount(coupon, subtotal, attendu):
    assert coupon_discount(subtotal, coupon) == attendu

def test_coupon_inconnu():
    with pytest.raises(ValueError):
        coupon_discount(Decimal("20.00"), "inconnu")

@pytest.mark.parametrize("amount_after_discount, coupon, empty, attendu", [
    (Decimal("0.00"), "WELCOME10", True, Decimal("0.00")),
    (Decimal("0.00"), "FREESHIP", False, Decimal("0.00")),
    (Decimal("50.00"), "", False, Decimal("0.00")),
    (Decimal("49.99"), "", False, Decimal("4.90")),
])
def test_shipping_cost(amount_after_discount, coupon, empty, attendu):
    assert shipping_cost(amount_after_discount, coupon, empty) == attendu

def test_livraison_payante_apres_remise():
    q = quote([{"product_id": "mug", "qty": 4}], "WELCOME10")
    assert q.subtotal == Decimal("50.00")
    assert q.shipping == Decimal("4.90")

def test_produit_inconnu():
    with pytest.raises(KeyError):
        quote([{"product_id": "nexistepas", "qty": 1}], None)

# TODO Atelier 1 :
#  - remise volume à partir de 10 unités (et pas à 9 !)
#  - quantités invalides (0, 100, -1, "2", True) -> ValueError   (astuce : @pytest.mark.parametrize)
#  - coupons WELCOME10 / FIXED5 / FREESHIP (seuils inclus/exclus), coupon inconnu, casse
#  - livraison offerte à partir de 50 € APRÈS remise
#  - produit inconnu -> KeyError
