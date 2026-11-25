from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import frappe
from frappe import _

GATEWAY_URL = "https://mcp.bom.frappe.cloud"
CLIENT_ID = "mcp-gateway"


@frappe.whitelist(methods=["GET"])
def return_to_connector(return_to: str):
	"""Send a user who signed in from an AI app back to the gateway, with this site's address."""
	if not is_gateway(return_to):
		frappe.throw(_("This app cannot connect to your CRM."), frappe.PermissionError)

	parts = urlsplit(return_to)
	query = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True) if key != "site"]
	query.append(("site", frappe.local.request.host))
	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = urlunsplit(parts._replace(query=urlencode(query)))


def gateway_url() -> str:
	"""The MCP gateway for ChatGPT and Claude. `mcp_gateway_url` in site config points a test site elsewhere."""
	return (frappe.conf.get("mcp_gateway_url") or GATEWAY_URL).rstrip("/")


def is_gateway(url: str) -> bool:
	parts, gateway = urlsplit(url), urlsplit(gateway_url())
	same_origin = (parts.scheme, parts.netloc.lower()) == (gateway.scheme, gateway.netloc.lower())
	return same_origin and not parts.fragment


def ensure_gateway_client():
	"""The public OAuth client the gateway signs users in with. Its only redirect is the gateway,
	so no other app can receive its codes."""
	values = gateway_client_values()
	if not frappe.db.exists("OAuth Client", CLIENT_ID):
		frappe.get_doc({"doctype": "OAuth Client", **values}).insert(
			ignore_permissions=True, set_name=CLIENT_ID
		)
		return

	client = frappe.get_doc("OAuth Client", CLIENT_ID)
	if any(client.get(key) != value for key, value in values.items()):
		client.update(values).save(ignore_permissions=True)


def gateway_client_values() -> dict:
	"""The user already allowed the AI app on the gateway's own page, so the site asks only for sign in."""
	redirect_uri = f"{gateway_url()}/site/callback"
	return {
		"app_name": "ChatGPT and Claude",
		"redirect_uris": redirect_uri,
		"default_redirect_uri": redirect_uri,
		"grant_type": "Authorization Code",
		"response_type": "Code",
		"token_endpoint_auth_method": "None",
		"scopes": "all",
		"skip_authorization": 1,
	}
