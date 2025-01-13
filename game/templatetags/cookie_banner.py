from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from django.urls import reverse

register = template.Library()


@register.simple_tag
def cookie_banner():
    ga_id = getattr(settings, 'GOOGLE_ANALYTICS_ID', 'G-CT610G0M3R')

    terms_url = reverse('terms_of_service')
    cookies_url = reverse('cookies_policy')

    banner_html = f'''
    <!-- Cookie Consent Modal -->
    <div class="modal fade" id="cookieConsentModal" tabindex="-1" aria-labelledby="cookieConsentModalLabel" aria-hidden="true" role="dialog">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content bg-dark text-white">
          <div class="modal-header border-0">
            <h5 class="modal-title" id="cookieConsentModalLabel">Cookie Consent</h5>
          </div>
          <div class="modal-body" id="cookieConsentModalDescription">
            <p>
              We use cookies to enhance your experience. By continuing to visit this site you agree to our use of cookies.
            </p>
            <p class="mb-0">
              For more information, please visit our <a href="{terms_url}" class="text-warning">Terms of Service</a> and <a href="{cookies_url}" class="text-warning">Cookies Policy</a>.
            </p>
          </div>
          <div class="modal-footer border-0 d-flex w-100 gap-2">
            <button type="button" id="essentialOnly" class="btn btn-secondary flex-fill btn-essential">Essential</button>
            <button type="button" id="acceptCookies" class="btn btn-success flex-fill btn-accept">Accept</button>
          </div>
        </div>
      </div>
    </div>

    <script>
    document.addEventListener("DOMContentLoaded", function() {{
        const cookieConsentModalElement = document.getElementById('cookieConsentModal');
        const cookieConsentModal = new bootstrap.Modal(cookieConsentModalElement, {{
            backdrop: 'static',
            keyboard: false
        }});

        const acceptBtn = document.getElementById('acceptCookies');
        const essentialBtn = document.getElementById('essentialOnly');
        const gaId = "{ga_id}";  // GA Measurement ID

        function setCookie(name, value, days) {{
            const date = new Date();
            date.setTime(date.getTime() + (days*24*60*60*1000));
            const expires = "expires=" + date.toUTCString();
            console.log(`Cookie set: ${{name}}=${{value}}; expires=${{expires}}; path=/;SameSite=Lax;Secure`);
            document.cookie = name + "=" + value + ";" + expires + ";path=/;SameSite=Lax;Secure";
        }}

        function getCookie(name) {{
            const cname = name + "=";
            const decodedCookie = decodeURIComponent(document.cookie);
            const ca = decodedCookie.split(';');
            for (let i = 0; i < ca.length; i++) {{
                let c = ca[i].trim();
                if (c.indexOf(cname) == 0) {{
                    console.log(`Cookie found: ${{name}}=${{c.substring(cname.length, c.length)}}`);
                    return c.substring(cname.length, c.length);
                }}
            }}
            console.log(`Cookie not found: ${{name}}`);
            return "";
        }}

        function loadGoogleAnalytics() {{
            if (!document.getElementById('ga-script') && gaId) {{
                console.log("Loading Google Analytics...");
                const script1 = document.createElement('script');
                script1.id = 'ga-script';
                script1.async = true;
                script1.src = `https://www.googletagmanager.com/gtag/js?id=${{gaId}}`;
                document.head.appendChild(script1);

                const script2 = document.createElement('script');
                script2.innerHTML = `
                    window.dataLayer = window.dataLayer || [];
                    function gtag(){{dataLayer.push(arguments);}}
                    gtag('js', new Date());
                    gtag('config', '${{gaId}}');
                `;
                document.head.appendChild(script2);
                console.log("Google Analytics scripts loaded.");
            }} else {{
                console.log("Google Analytics already loaded or GA ID not set.");
            }}
        }}

        const consent = getCookie("cookieConsent");

        if (!consent) {{
            console.log("No consent found. Showing cookie consent modal.");
            cookieConsentModal.show();
        }} else if (consent === "accepted") {{
            console.log("Consent found: accepted. Loading Google Analytics.");
            loadGoogleAnalytics();
        }} else if (consent === "essential") {{
            console.log("Consent found: essential. Essential scripts only.");
            // No GA load
        }} else {{
            console.log(`Unknown consent value: ${{consent}}. Showing cookie consent modal.`);
            cookieConsentModal.show();
        }}

        acceptBtn.addEventListener('click', function() {{
            setCookie("cookieConsent", "accepted", 365);
            console.log("User accepted cookies.");
            cookieConsentModal.hide();
            loadGoogleAnalytics();
        }});

        essentialBtn.addEventListener('click', function() {{
            setCookie("cookieConsent", "essential", 365);
            console.log("User chose essential cookies only.");
            cookieConsentModal.hide();
            // Load essential scripts if any
        }});
    }});
    </script>
    '''
    return mark_safe(banner_html)