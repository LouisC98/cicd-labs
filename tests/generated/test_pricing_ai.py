"""Tests générés par LLM (Claude, via la session) depuis specs/pricing.feature.

Moteur : LLM, prompt ai_tools/prompts/generate_tests.md, source minishop/pricing.py.
Tests de cas limites préfixés par `test_limite_`.
"""

from decimal import Decimal

import pytest

from minishop.pricing import money, quote

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
    """Dès 10 unités du même produit, la ligne bénéficie de -5 %."""
    q = quote([{"product_id": "sticker", "qty": 10}])
    assert q.subtotal == Decimal("23.28")


def test_coupon_de_bienvenue():
    """WELCOME10 retire 10 % du sous-total quand il atteint 20 €."""
    q = quote([{"product_id": "mug", "qty": 2}], "WELCOME10")
    assert q.discount == Decimal("2.50")
    assert q.total == Decimal("27.40")


def test_coupon_de_bienvenue_sous_le_seuil():
    """WELCOME10 n'apporte aucune remise si le sous-total est sous 20 €."""
    q = quote([{"product_id": "mug", "qty": 1}], "WELCOME10")
    assert q.discount == Decimal("0.00")


def test_coupon_de_livraison_offerte():
    """FREESHIP annule les frais de livraison sans remise sur le produit."""
    q = quote([{"product_id": "sticker", "qty": 1}], "FREESHIP")
    assert q.shipping == Decimal("0.00")
    assert q.total == Decimal("2.45")


def test_coupon_inconnu():
    """Un code coupon absent de la liste lève une erreur « Coupon inconnu »."""
    with pytest.raises(ValueError, match="Coupon inconnu"):
        quote([{"product_id": "mug", "qty": 1}], "NOEL2026")


def test_produit_inconnu():
    """Un identifiant de produit absent du catalogue lève une KeyError « Produit inconnu »."""
    with pytest.raises(KeyError, match="Produit inconnu"):
        quote([{"product_id": "licorne", "qty": 1}])


def test_fixed5_au_seuil():
    """FIXED5 n'apporte aucune remise avec un seul livre (29,99 € < 30 €)."""
    q = quote([{"product_id": "book", "qty": 1}], "FIXED5")
    assert q.discount == Decimal("0")


def test_remise_volume_des_10_unites_et_coupon_welcome10():
    """La remise volume et WELCOME10 se cumulent : le coupon porte sur le sous-total déjà remisé."""
    q = quote([{"product_id": "sticker", "qty": 10}], "WELCOME10")
    assert q.discount == Decimal("2.33")
    assert q.total == Decimal("25.85")


def test_quantite_zero_refusee():
    """Une quantité de 0 lève une erreur « Quantité hors limites »."""
    with pytest.raises(ValueError, match="Quantité hors limites"):
        quote([{"product_id": "mug", "qty": 0}])


# --------------------------------------------------------------------------- cas limites (non cités par la spec)


def test_limite_remise_volume_absente_a_9_unites():
    """La remise volume ne s'applique qu'à partir de 10 unités, pas à 9."""
    q = quote([{"product_id": "sticker", "qty": 9}])
    assert q.subtotal == Decimal("22.05")


def test_limite_quantite_maximale_99_acceptee():
    """99 unités est la quantité maximale acceptée, avec remise volume."""
    q = quote([{"product_id": "sticker", "qty": 99}])
    assert q.subtotal == Decimal("230.42")


@pytest.mark.parametrize("qty", [-1, 100])
def test_limite_quantite_hors_bornes_refusee(qty):
    """Une quantité négative ou supérieure à 99 est refusée."""
    with pytest.raises(ValueError, match="Quantité hors limites"):
        quote([{"product_id": "mug", "qty": qty}])


@pytest.mark.parametrize("qty", [True, 1.5, "2"])
def test_limite_quantite_non_entiere_refusee(qty):
    """Une quantité qui n'est pas un entier (booléen, flottant, chaîne) est refusée."""
    with pytest.raises(ValueError, match="entier"):
        quote([{"product_id": "mug", "qty": qty}])


def test_limite_livraison_exactement_au_seuil_de_50():
    """Un total exactement égal à 50,00 € donne la livraison offerte (seuil inclus)."""
    q = quote([{"product_id": "mug", "qty": 4}])
    assert q.subtotal == Decimal("50.00")
    assert q.shipping == Decimal("0.00")


def test_limite_livraison_payante_juste_sous_le_seuil():
    """Un total de 37,50 € (sous 50 €) paie la livraison de 4,90 €."""
    q = quote([{"product_id": "mug", "qty": 3}])
    assert q.shipping == Decimal("4.90")
    assert q.total == Decimal("42.40")


def test_limite_welcome10_sous_le_seuil_de_20_euros():
    """À 19,60 € (8 stickers), WELCOME10 ne s'applique pas."""
    q = quote([{"product_id": "sticker", "qty": 8}], "WELCOME10")
    assert q.discount == Decimal("0.00")


def test_limite_welcome10_au_dessus_du_seuil_arrondi_demi_superieur():
    """À 22,05 € (9 stickers), WELCOME10 retire 2,205 € arrondis à 2,21 €."""
    q = quote([{"product_id": "sticker", "qty": 9}], "WELCOME10")
    assert q.discount == Decimal("2.21")
    assert q.total == Decimal("24.74")


def test_limite_fixed5_au_dessus_du_seuil_de_30_euros():
    """À 32,40 € (mug + tshirt), FIXED5 retire 5,00 €."""
    q = quote([{"product_id": "mug", "qty": 1}, {"product_id": "tshirt", "qty": 1}], "FIXED5")
    assert q.discount == Decimal("5.00")
    assert q.total == Decimal("32.30")


@pytest.mark.parametrize("coupon", ["welcome10", "  WELCOME10  ", "Welcome10"])
def test_limite_code_coupon_insensible_a_la_casse_et_aux_espaces(coupon):
    """Le code coupon est normalisé (casse et espaces ignorées)."""
    q = quote([{"product_id": "mug", "qty": 2}], coupon)
    assert q.discount == Decimal("2.50")


def test_limite_coupon_vide_sans_remise():
    """Une chaîne de coupon vide équivaut à l'absence de coupon."""
    q = quote([{"product_id": "mug", "qty": 2}], "")
    assert q.discount == Decimal("0.00")
    assert q.total == Decimal("29.90")


def test_limite_student15_hors_spec():
    """# HORS SPEC : STUDENT15 existe dans le code mais pas dans specs/pricing.feature.

    Sur 2 mugs (25,00 €) : -15 % = 3,75 €, livraison de 4,90 € payée.
    """
    q = quote([{"product_id": "mug", "qty": 2}], "STUDENT15")
    assert q.discount == Decimal("3.75")
    assert q.total == Decimal("26.15")


def test_limite_student15_non_cumulable_avec_la_remise_volume():
    """STUDENT15 ne s'applique pas aux lignes déjà en remise volume (10 stickers seuls : 0 €)."""
    q = quote([{"product_id": "sticker", "qty": 10}], "STUDENT15")
    assert q.discount == Decimal("0.00")
    assert q.subtotal == Decimal("23.28")


def test_limite_student15_applique_uniquement_aux_lignes_hors_volume():
    """Mélange 10 stickers (remise volume) et 1 mug : STUDENT15 ne porte que sur le mug (12,50 €)."""
    q = quote([{"product_id": "sticker", "qty": 10}, {"product_id": "mug", "qty": 1}], "STUDENT15")
    assert q.discount == Decimal("1.88")
    assert q.total == Decimal("38.80")


def test_limite_coupon_inconnu_insensible_a_la_casse():
    """Un coupon inconnu reste refusé quelle que soit sa casse."""
    with pytest.raises(ValueError, match="Coupon inconnu"):
        quote([{"product_id": "mug", "qty": 1}], "noel2026")


@pytest.mark.parametrize(
    ("brut", "attendu"),
    [
        (Decimal("0.125"), Decimal("0.13")),
        (Decimal("0.124"), Decimal("0.12")),
        (Decimal("2.345"), Decimal("2.35")),
    ],
)
def test_limite_arrondi_commercial_demi_superieur(brut, attendu):
    """L'arrondi au centime est commercial (ROUND_HALF_UP) : 0,125 devient 0,13."""
    assert money(brut) == attendu
