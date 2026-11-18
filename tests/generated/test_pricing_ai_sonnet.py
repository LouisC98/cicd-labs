"""Tests générés à partir de specs/pricing.feature et minishop/pricing.py."""

from decimal import Decimal

import pytest

from minishop.pricing import coupon_discount, line_total, money, quote

pytestmark = [pytest.mark.generated, pytest.mark.unit]

D = Decimal


def items(*pairs):
    """Construit une liste d'items {product_id, qty} à partir de couples (produit, quantité)."""
    return [{"product_id": p, "qty": q} for p, q in pairs]


# --------------------------------------------------------------------------
# Scénarios de la spécification
# --------------------------------------------------------------------------


def test_panier_vide():
    """Un panier vide a un total nul et aucun frais de livraison."""
    q = quote([])
    assert q.total == D("0.00")
    assert q.shipping == D("0.00")


def test_achat_simple_avec_frais_de_livraison():
    """Sous 50 €, la livraison coûte 4,90 € et s'ajoute au sous-total."""
    q = quote(items(("mug", 2)))
    assert q.subtotal == D("25.00")
    assert q.shipping == D("4.90")
    assert q.total == D("29.90")


def test_livraison_offerte_a_partir_de_50_euros():
    """Dès 50 € après remise, la livraison est offerte."""
    q = quote(items(("hoodie", 1), ("mug", 1)))
    assert q.shipping == D("0.00")
    assert q.total == D("56.50")


def test_remise_volume_des_10_unites():
    """Dès 10 unités d'un même produit, la ligne bénéficie de -5 %."""
    q = quote(items(("sticker", 10)))
    assert q.subtotal == D("23.28")


def test_coupon_de_bienvenue():
    """WELCOME10 retire 10 % du sous-total quand il atteint 20 €."""
    q = quote(items(("mug", 2)), "WELCOME10")
    assert q.discount == D("2.50")
    assert q.total == D("27.40")


def test_coupon_de_bienvenue_sous_le_seuil():
    """WELCOME10 n'apporte aucune remise sous 20 € de sous-total."""
    q = quote(items(("mug", 1)), "WELCOME10")
    assert q.discount == D("0.00")


def test_coupon_de_livraison_offerte():
    """FREESHIP offre la livraison même sous le seuil de 50 €."""
    q = quote(items(("sticker", 1)), "FREESHIP")
    assert q.shipping == D("0.00")
    assert q.total == D("2.45")


def test_coupon_inconnu():
    """Un code coupon inconnu lève une ValueError."""
    with pytest.raises(ValueError, match="Coupon inconnu"):
        quote(items(("mug", 1)), "NOEL2026")


def test_produit_inconnu():
    """Un produit absent du catalogue est refusé avec le message « Produit inconnu »."""
    # DIVERGENCE SPEC/CODE : le code lève une KeyError (via get_product) et non une ValueError.
    with pytest.raises(KeyError, match="Produit inconnu"):
        quote(items(("licorne", 1)))


def test_fixed5_au_seuil():
    """FIXED5 ne donne aucune remise quand le sous-total (29,99 €) est sous 30 €."""
    q = quote(items(("book", 1)), "FIXED5")
    assert q.discount == D("0")


def test_remise_volume_des_10_unites_et_coupon_welcome10():
    """La remise volume et WELCOME10 se cumulent : 10 % de 23,28 € = 2,33 €."""
    q = quote(items(("sticker", 10)), "WELCOME10")
    assert q.discount == D("2.33")
    assert q.total == D("25.85")


def test_quantite_zero_refusee():
    """Une quantité de 0 est hors limites et lève une ValueError."""
    with pytest.raises(ValueError, match="Quantité hors limites"):
        quote(items(("mug", 0)))


# --------------------------------------------------------------------------
# Cas limites
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("qty", "expected"),
    [
        (9, D("22.05")),   # 9 x 2,45 : pas de remise volume
        (10, D("23.28")),  # 24,50 x 0,95 = 23,275 -> 23,28 (borne incluse)
        (11, D("25.60")),  # 26,95 x 0,95 = 25,6025
    ],
)
def test_limite_seuil_remise_volume(qty, expected):
    """La remise volume s'applique à partir de 10 unités incluses, pas à 9."""
    assert quote(items(("sticker", qty))).subtotal == expected


@pytest.mark.parametrize("qty", [1, 99])
def test_limite_quantites_valides_aux_bornes(qty):
    """Les quantités 1 et 99 sont acceptées."""
    assert quote(items(("mug", qty))).lines[0].qty == qty


@pytest.mark.parametrize("qty", [0, -1, 100, 1000])
def test_limite_quantite_hors_bornes(qty):
    """Une quantité inférieure à 1 ou supérieure à 99 lève une ValueError."""
    with pytest.raises(ValueError, match="Quantité hors limites"):
        quote(items(("mug", qty)))


@pytest.mark.parametrize("qty", [1.0, "2", None, True])
def test_limite_quantite_non_entiere(qty):
    """Une quantité qui n'est pas un entier (ni un booléen) lève une ValueError."""
    with pytest.raises(ValueError, match="entier"):
        quote(items(("mug", qty)))


def test_limite_quantite_maximale_avec_remise_volume():
    """99 stickers : 242,55 x 0,95 = 230,4225 arrondi à 230,42, livraison offerte."""
    q = quote(items(("sticker", 99)))
    assert q.subtotal == D("230.42")
    assert q.shipping == D("0.00")
    assert q.total == D("230.42")


def test_limite_livraison_offerte_pile_a_50_euros():
    """Le seuil de livraison offerte est inclus : 4 mugs = 50,00 € donc livraison 0."""
    q = quote(items(("mug", 4)))
    assert q.subtotal == D("50.00")
    assert q.shipping == D("0.00")
    assert q.total == D("50.00")


def test_limite_livraison_payante_juste_sous_50_euros():
    """À 48,90 € (hoodie + 2 stickers), la livraison de 4,90 € s'applique."""
    q = quote(items(("hoodie", 1), ("sticker", 2)))
    assert q.subtotal == D("48.90")
    assert q.shipping == D("4.90")
    assert q.total == D("53.80")


def test_limite_seuil_livraison_evalue_apres_remise():
    """4 mugs avec WELCOME10 passent à 45 € après remise : la livraison redevient payante."""
    q = quote(items(("mug", 4)), "WELCOME10")
    assert q.discount == D("5.00")
    assert q.shipping == D("4.90")
    assert q.total == D("49.90")


@pytest.mark.parametrize(
    ("subtotal", "expected"),
    [
        (D("19.99"), D("0.00")),  # juste sous le seuil
        (D("20.00"), D("2.00")),  # seuil inclus
        (D("20.05"), D("2.01")),  # 2,005 -> 2,01 (arrondi commercial)
    ],
)
def test_limite_seuil_welcome10(subtotal, expected):
    """WELCOME10 s'applique à partir de 20 € inclus, avec arrondi au centime supérieur."""
    assert coupon_discount(subtotal, "WELCOME10") == expected


@pytest.mark.parametrize(
    ("subtotal", "expected"),
    [
        (D("29.99"), D("0.00")),
        (D("30.00"), D("5.00")),
        (D("100.00"), D("5.00")),
    ],
)
def test_limite_seuil_fixed5(subtotal, expected):
    """FIXED5 retire 5 € fixes à partir de 30 € inclus, rien en dessous."""
    assert coupon_discount(subtotal, "FIXED5") == expected


def test_limite_fixed5_applique_au_dessus_du_seuil():
    """Livre + sticker (32,44 €) : FIXED5 retire 5 € et le total devient 32,34 €."""
    q = quote(items(("book", 1), ("sticker", 1)), "FIXED5")
    assert q.subtotal == D("32.44")
    assert q.discount == D("5.00")
    assert q.total == D("32.34")


@pytest.mark.parametrize("coupon", ["welcome10", " WELCOME10 ", "Welcome10"])
def test_limite_coupon_insensible_casse_et_espaces(coupon):
    """Le code coupon est normalisé (majuscules, espaces retirés)."""
    q = quote(items(("mug", 2)), coupon)
    assert q.coupon == "WELCOME10"
    assert q.discount == D("2.50")


@pytest.mark.parametrize("coupon", [None, ""])
def test_limite_sans_coupon(coupon):
    """Sans coupon (None ou chaîne vide), aucune remise n'est appliquée."""
    q = quote(items(("mug", 2)), coupon)
    assert q.coupon is None
    assert q.discount == D("0.00")
    assert q.total == D("29.90")


def test_limite_freeship_insensible_a_la_casse():
    """FREESHIP en minuscules offre aussi la livraison."""
    q = quote(items(("mug", 1)), "freeship")
    assert q.shipping == D("0.00")
    assert q.total == D("12.50")


def test_limite_coupon_inconnu_via_coupon_discount():
    """coupon_discount rejette directement un code inconnu."""
    with pytest.raises(ValueError, match="Coupon inconnu"):
        coupon_discount(D("10.00"), "BIDON")


def test_limite_panier_vide_avec_coupon_connu():
    """Un panier vide avec un coupon valide reste à zéro, sans remise ni livraison."""
    q = quote([], "WELCOME10")
    assert q.discount == D("0.00")
    assert q.shipping == D("0.00")
    assert q.total == D("0.00")


def test_limite_student15_sans_remise_volume():
    """STUDENT15 retire 15 % : 1,875 € arrondi à 1,88 € sur un mug."""
    # DIVERGENCE SPEC/CODE : STUDENT15 est implémenté dans le code mais absent de la
    # spécification et de la docstring du module ; le comportement testé est celui du code.
    q = quote(items(("mug", 1)), "STUDENT15")
    assert q.discount == D("1.88")
    assert q.total == D("15.52")


def test_limite_student15_non_cumulable_avec_remise_volume():
    """STUDENT15 ne s'applique pas aux lignes déjà remisées par le volume (10 unités ou plus)."""
    # DIVERGENCE SPEC/CODE : règle absente de la spécification (voir commit « STUDENT15 non cumulable »).
    q = quote(items(("sticker", 10), ("mug", 1)), "STUDENT15")
    assert q.subtotal == D("35.78")
    assert q.discount == D("1.88")  # 15 % de 12,50 € uniquement
    assert q.total == D("38.80")


def test_limite_student15_seulement_lignes_volume():
    """Avec uniquement des lignes à remise volume, STUDENT15 n'apporte aucune remise."""
    # DIVERGENCE SPEC/CODE : règle absente de la spécification.
    q = quote(items(("sticker", 10)), "STUDENT15")
    assert q.discount == D("0.00")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (D("0.125"), D("0.13")),  # arrondi commercial, pas arrondi bancaire (0,12)
        (D("0.135"), D("0.14")),
        (D("0.005"), D("0.01")),
        (D("0.004"), D("0.00")),
        (2.675, D("2.68")),       # float converti via str : pas d'artefact binaire
        ("1.005", D("1.01")),
        (3, D("3.00")),
    ],
)
def test_limite_arrondi_commercial(value, expected):
    """money arrondit au centime avec ROUND_HALF_UP (la moitié part vers le haut)."""
    assert money(value) == expected


def test_limite_line_total_applique_la_remise_volume():
    """line_total applique -5 % dès 10 unités et arrondit au centime."""
    assert line_total(D("2.45"), 9) == D("22.05")
    assert line_total(D("2.45"), 10) == D("23.28")


def test_limite_plusieurs_lignes_cumulees():
    """Le sous-total est la somme des totaux de ligne, chacun arrondi séparément."""
    q = quote(items(("mug", 2), ("tshirt", 1), ("sticker", 10)))
    assert [ln.total for ln in q.lines] == [D("25.00"), D("19.90"), D("23.28")]
    assert q.subtotal == D("68.18")
    assert q.shipping == D("0.00")
    assert q.total == D("68.18")


def test_limite_as_dict_serialise_les_montants_en_chaines():
    """as_dict expose les montants sous forme de chaînes et le coupon normalisé."""
    d = quote(items(("mug", 2)), "welcome10").as_dict()
    assert d == {
        "lines": [{"product_id": "mug", "qty": 2, "unit_price": "12.50", "total": "25.00"}],
        "subtotal": "25.00",
        "discount": "2.50",
        "shipping": "4.90",
        "total": "27.40",
        "coupon": "WELCOME10",
    }
