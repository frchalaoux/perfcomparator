"""Repères locaux pour afficher l'année de commercialisation des Mac Apple."""

from __future__ import annotations

# Vérifiés dans les pages Apple « Identifier votre modèle » des gammes MacBook
# Pro, MacBook Air, iMac, Mac mini, Mac Studio et Mac Pro. Les identifiants
# absents de cette table restent volontairement sans année.
_MODEL_YEARS = {
    "iMacPro1,1": 2017,
    "MacBookAir8,1": 2018,
    "MacBookAir8,2": 2019,
    "MacBookAir9,1": 2020,
    "MacBookAir10,1": 2020,
    "MacBookPro13,1": 2016,
    "MacBookPro13,2": 2016,
    "MacBookPro13,3": 2016,
    "MacBookPro14,1": 2017,
    "MacBookPro14,2": 2017,
    "MacBookPro14,3": 2017,
    "MacBookPro15,4": 2019,
    "MacBookPro16,1": 2019,
    "MacBookPro16,2": 2020,
    "MacBookPro16,3": 2020,
    "MacBookPro16,4": 2019,
    "MacBookPro17,1": 2020,
    "MacBookPro18,1": 2021,
    "MacBookPro18,2": 2021,
    "MacBookPro18,3": 2021,
    "MacBookPro18,4": 2021,
    "Mac14,2": 2022,
    "Mac14,3": 2023,
    "Mac14,5": 2023,
    "Mac14,6": 2023,
    "Mac14,7": 2022,
    "Mac14,8": 2023,
    "Mac14,9": 2023,
    "Mac14,10": 2023,
    "Mac14,12": 2023,
    "Mac14,13": 2023,
    "Mac14,14": 2023,
    "Mac14,15": 2023,
    "Mac15,4": 2023,
    "Mac15,12": 2024,
    "Mac15,13": 2024,
    "Mac16,3": 2024,
    "Mac16,12": 2025,
    "Mac16,13": 2025,
    "Mac17,3": 2026,
    "Mac17,4": 2026,
    "MacPro7,1": 2019,
    "Macmini8,1": 2018,
    "Macmini9,1": 2020,
    "iMac21,1": 2021,
    "iMac21,2": 2021,
    "Mac13,1": 2022,
    "Mac13,2": 2022,
}

# Ces identifiants sont réutilisés entre les générations 2018 et 2019. Les
# références Apple officielles les distinguent sans exposer de numéro de série.
_AMBIGUOUS_2018_2019 = frozenset({"MacBookPro15,1", "MacBookPro15,2", "MacBookPro15,3"})


def apple_model_year(model_identifier: str, product_sku: str | None = None) -> int | None:
    """Retourne l'année de commercialisation connue, sinon ``None``."""
    if model_identifier in _AMBIGUOUS_2018_2019:
        sku = (product_sku or "").upper()
        if sku.startswith(("MR", "MUQ")):
            return 2018
        if sku.startswith("MV9"):
            return 2019
        return None
    return _MODEL_YEARS.get(model_identifier)
