import os
from typing import List, Optional

from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import AzureError


class AzureOCRService:
    """
    OCR rapide via Azure Document Intelligence (ex-Form Recognizer) – modèle 'prebuilt-read'.
    Attend AZURE_VISION_ENDPOINT et AZURE_VISION_KEY dans l'environnement (ou .env).
    """

    def __init__(self) -> None:
        endpoint = os.getenv("AZURE_VISION_ENDPOINT")
        key = os.getenv("AZURE_VISION_KEY")

        if not endpoint or not key:
            raise RuntimeError(
                "AZURE_VISION_ENDPOINT / AZURE_VISION_KEY manquants. "
                "Ajoute-les dans ton .env (ou variables d’environnement)."
            )

        self.client = DocumentAnalysisClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key),
        )

    def ocr_bytes(self, data: bytes) -> str:
        """
        Extrait le texte d’une image (bytes) avec le modèle 'prebuilt-read'.
        Retourne une chaîne avec des sauts de ligne.
        """
        try:
            poller = self.client.begin_analyze_document(
                model_id="prebuilt-read",
                document=data,
                locales=["fr", "en"]  # adapte si tu veux forcer uniquement 'fr'
            )
            result = poller.result()
            return self._to_text(result)
        except AzureError as e:
            raise RuntimeError(f"OCR Azure a échoué: {e}") from e

    @staticmethod
    def _to_text(result) -> str:
        """
        Concatène les lignes trouvées par le modèle 'prebuilt-read'.
        """
        lines: List[str] = []
        # result.documents est vide pour prebuilt-read; le texte est dans result.paragraphs/lines
        if getattr(result, "pages", None):
            for page in result.pages:
                if getattr(page, "lines", None):
                    for line in page.lines:
                        if line.content:
                            lines.append(line.content)
        # fallback possible: result.paragraphs
        if not lines and getattr(result, "paragraphs", None):
            for p in result.paragraphs:
                if p.content:
                    lines.append(p.content)
        return "\n".join(lines).strip()
