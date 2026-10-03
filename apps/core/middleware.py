class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; object-src 'none'"
        )
        response.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if (
            "/account/" in request.path
            or "/agency/" in request.path
            or "/admin/" in request.path
            or request.user.is_authenticated
        ):
            response["Cache-Control"] = "private, no-store"
        return response


class AccountGateMiddleware:
    """Gate private operations, keeping legal/recovery/logout paths available."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.user.is_authenticated:
            return None
        from django.contrib.auth import logout
        from django.shortcuts import redirect

        from .accounts import ACCOUNT_DOCUMENTS, docs
        from .models import LegalAcceptance

        if not request.user.email_verified_at:
            logout(request)
            return redirect("login")
        # Language variants of the same version count as the same accepted contract.
        match = request.resolver_match
        allowed = {
            "health",
            "home",
            "legal_index",
            "legal_document",
            "logout",
            "login",
            "signup",
            "recover",
            "resend",
            "account_token",
            "accept_current",
            "mfa_enroll",
            "mfa_challenge",
        }
        if match and match.url_name not in allowed:
            current = docs(getattr(request, "LANGUAGE_CODE", "es"))
            accepted = set(
                LegalAcceptance.objects.filter(user=request.user).values_list(
                    "document__slug", "document__version"
                )
            )
            if len(current) != len(ACCOUNT_DOCUMENTS) or any(
                (doc.slug, doc.version) not in accepted for doc in current
            ):
                return redirect("accept_current")
            from .mfa import requires_mfa

            if requires_mfa(request.user) and (
                not request.user.mfa_enabled
                or request.session.get("mfa_version") != request.user.mfa_version
            ):
                return redirect("mfa_enroll" if not request.user.mfa_enabled else "mfa_challenge")
        return None
