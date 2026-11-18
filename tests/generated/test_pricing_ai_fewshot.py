"""Tests générés par LLM (Claude, via la session) depuis specs/pricing.feature.

Moteur : LLM, prompt ai_tools/prompts/generate_tests.md, source minishop/pricing.py.
Variante « few-shot » : style calqué sur l'exemple fourni (seuils testés pile et juste en dessous).
Tests de cas limites préfixés par `test_limite_`.
"""

from decimal import Decimal

import pytest

from minishop.pricing import coupon_discount, line_total, money, quote, shipping_cost

pytestmark = [pytest.mark.generated, pytest.mark.unit]


# --------------------------------------------------------------------------- scénarios de la spec


def test_panier_vide():
    """Un panier vide a un total de 0 et aucun frais de livraison."""
    q = quote([])
    assert q.total == Decimal("0.00")
    assert q.shipping == Decimal("0.00")


def test_achat_simple_avec_frais_de_livraison():
    """Sous 50 € après remise, la livraison de 4,90 € est facturée."""
    q = quote([{"product_id": "mug", "qty": 2}])
    assert q.subtotal == Decimal("25.00")
    assert q.shipping == Decimal("4.90")
    assert q.total == Decimal("29.90")


def test_livraison_offerte_a_partir_de_50_euros():
    """Un total d'au moins 50 € après remise donne une livraison offerte."""
    q = quote([{"product_id": "hoodie", "qty": 1}, {"product_id": "mug", "qty": 1}])
    assert q.shipping == Decimal("0.00")
    assert q.total == Decimal("56.50")


def test_remise_volume_des_10_unites():
    """Dès 10 unités du même produit, une remise de 5 % s'applique à la ligne."""
    q = quote([{"product_id": "sticker", "qty": 10}])
    assert q.subtotal == Decimal("23.28")


def test_coupon_de_bienvenue():
    """WELCOME10 retire 10 % du sous-total lorsque celui-ci atteint 20 €."""
    q = quote([{"product_id": "mug", "qty": 2}], "WELCOME10")
    assert q.discount == Decimal("2.50")
    assert q.total == Decimal("27.40")


def test_coupon_de_bienvenue_sous_le_seuil():
    """WELCOME10 n'apporte aucune remise sous un sous-total de 20 €."""
    q = quote([{"product_id": "mug", "qty": 1}], "WELCOME10")
    assert q.discount == Decimal("0.00")


def test_coupon_de_livraison_offerte():
    """FREESHIP supprime les frais de livraison, même sous 50 €."""
    q = quote([{"product_id": "sticker", "qty": 1}], "FREESHIP")
    assert q.shipping == Decimal("0.00")
    assert q.total == Decimal("2.45")


def test_coupon_inconnu():
    """Un code coupon absent de la liste connue lève une ValueError."""
    with pytest.raises(ValueError, match="Coupon inconnu"):
        quote([{"product_id": "mug", "qty": 1}], "NOEL2026")


def test_produit_inconnu():
    """Un identifiant produit absent du catalogue lève une erreur « Produit inconnu »."""
    with pytest.raises(KeyError, match="Produit inconnu"):
        quote([{"product_id": "licorne", "qty": 1}])


def test_fixed5_au_seuil():
    """FIXED5 n'apporte aucune remise pour un sous-total de 29,99 € (sous le seuil de 30 €)."""
    q = quote([{"product_id": "book", "qty": 1}], "FIXED5")
    assert q.discount == Decimal("0")


def test_remise_volume_des_10_unites_et_coupon_welcome10():
    """La remise volume et WELCOME10 se cumulent : le coupon porte sur le sous-total déjà remisé."""
    q = quote([{"product_id": "sticker", "qty": 10}], "WELCOME10")
    assert q.discount == Decimal("2.33")
    assert q.total == Decimal("25.85")


def test_quantite_zero_refusee():
    """Une quantité de 0 est refusée par une ValueError « Quantité hors limites »."""
    with pytest.raises(ValueError, match="Quantité hors limites"):
        quote([{"product_id": "mug", "qty": 0}])


# --------------------------------------------------------------------------- cas limites (hors spec)


@pytest.mark.parametrize(
    "subtotal, attendu",
    [
        (Decimal("19.99"), Decimal("0.00")),
        (Decimal("20.00"), Decimal("2.00")),
    ],
)
def test_limite_welcome10_seuil_20_euros(subtotal, attendu):
    """WELCOME10 s'active exactement à 20,00 € et pas en dessous."""
    assert coupon_discount(subtotal, "WELCOME10") == attendu


@pytest.mark.parametrize(
    "subtotal, attendu",
    [
        (Decimal("29.99"), Decimal("0.00")),
        (Decimal("30.00"), Decimal("5.00")),
    ],
)
def test_limite_fixed5_seuil_30_euros(subtotal, attendu):
    """FIXED5 s'active exactement à 30,00 € et pas en dessous."""
    assert coupon_discount(subtotal, "FIXED5") == attendu


@pytest.mark.parametrize(
    "qty, attendu",
    [
        (9, Decimal("22.05")),
        (10, Decimal("23.28")),
    ],
)
def test_limite_remise_volume_seuil_10_unites(qty, attendu):
    """La remise volume de 5 % commence à 10 unités, pas à 9."""
    assert line_total(Decimal("2.45"), qty) == attendu


@pytest.mark.parametrize(
    "qty, attendu",
    [
        (1, Decimal("2.45")),
        (99, Decimal("230.42")),
    ],
)
def test_limite_quantite_bornes_valides(qty, attendu):
    """Les bornes 1 et 99 sont acceptées ; 99 unités avec remise volume s'arrondissent au centime."""
    assert line_total(Decimal("2.45"), qty) == attendu


@pytest.mark.parametrize("qty", [0, -1, 100])
def test_limite_quantite_hors_bornes(qty):
    """Une quantité sous 1 ou au-dessus de 99 lève une ValueError."""
    with pytest.raises(ValueError, match="Quantité hors limites"):
        line_total(Decimal("2.45"), qty)


@pytest.mark.parametrize("qty", [True, "2", 2.0])
def test_limite_quantite_non_entiere(qty):
    """Un booléen, une chaîne ou un flottant ne sont pas une quantité valide."""
    with pytest.raises(ValueError, match="entier"):
        line_total(Decimal("2.45"), qty)


@pytest.mark.parametrize(
    "montant, attendu",
    [
        (Decimal("49.99"), Decimal("4.90")),
        (Decimal("50.00"), Decimal("0.00")),
    ],
)
def test_limite_livraison_seuil_50_euros(montant, attendu):
    """La livraison est offerte exactement à 50,00 € et pas en dessous."""
    assert shipping_cost(montant, None, empty=False) == attendu


def test_limite_freeship_quel_que_soit_le_montant():
    """FREESHIP offre la livraison même pour un montant très faible."""
    assert shipping_cost(Decimal("1.00"), "FREESHIP", empty=False) == Decimal("0.00")


def test_limite_coupon_insensible_a_la_casse_et_aux_espaces():
    """Le code coupon est normalisé (espaces retirés, majuscules) avant comparaison."""
    assert coupon_discount(Decimal("20.00"), "  welcome10 ") == Decimal("2.00")
    assert quote([{"product_id": "mug", "qty": 2}], "welcome10").coupon == "WELCOME10"


@pytest.mark.parametrize("coupon", [None, ""])
def test_limite_coupon_absent_ou_vide_sans_remise(coupon):
    """Ni coupon (None) ni chaîne vide n'apportent de remise."""
    assert coupon_discount(Decimal("100.00"), coupon) == Decimal("0.00")


@pytest.mark.parametrize(
    "valeur, attendu",
    [
        ("0.125", Decimal("0.13")),
        ("2.345", Decimal("2.35")),
    ],
)
def test_limite_arrondi_commercial_demi_centime(monkeypatch, valeur, attendu):
    """Un demi-centime s'arrondit vers le haut (ROUND_HALF_UP), même quand le chiffre précédent est pair."""
    monkeypatch.delenv("MINISHOP_BUG", raising=False)
    assert money(valeur) == attendu


def test_limite_student15_exclut_les_lignes_en_remise_volume():
    """STUDENT15 ne s'applique qu'aux lignes sous le seuil de remise volume, sans cumul."""
    q = quote(
        [{"product_id": "sticker", "qty": 10}, {"product_id": "mug", "qty": 2}],
        "STUDENT15",
    )
    assert q.subtotal == Decimal("48.28")
    assert q.discount == Decimal("3.75")
