"""Fixed requester-facing questions; never interpolate case or staff evidence."""

PROMPTS = {
    "reference": (
        "Indica qué perfil o qué datos tuyos están relacionados con la solicitud. No incluyas documentos ni datos de terceros.",
        "Indicate which profile or which of your data relate to the request. Do not include documents or other people's data.",
    ),
    "scope": (
        "Aclara qué actuación solicitas y sobre qué datos tuyos. No incluyas documentos ni datos de terceros.",
        "Clarify the action you request and which of your data it concerns. Do not include documents or other people's data.",
    ),
    "contact": (
        "Si deseas facilitar un contacto, indica un canal propio al que tengas acceso. No pidas ayuda al gestor del perfil. Esto no comprueba identidad.",
        "If you wish to provide contact details, indicate your own accessible channel. Do not ask the profile manager for help. This does not verify identity.",
    ),
}
