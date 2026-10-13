import frappe


def complete_setup_for_fc_site(login_manager=None):
	"""Finish setup with the data Frappe Cloud prefilled at signup, so the desk wizard is skipped."""
	if not should_auto_complete_setup():
		return

	from frappe.desk.page.setup_wizard.setup_wizard import setup_complete

	try:
		setup_complete(get_prefilled_setup_args())
	except Exception:
		frappe.log_error("Frappe Cloud setup auto-complete failed")


CRM_SITE_APPS = {"frappe", "crm", "whatsapp"}


def should_auto_complete_setup():
	from frappe.core.doctype.installed_applications.installed_applications import has_non_admin_user
	from frappe.integrations.frappe_providers.frappecloud_billing import is_fc_site

	if frappe.is_setup_complete() or frappe.conf.skip_setup_wizard:
		return False
	# other apps may need their own wizard input
	if not set(frappe.get_installed_apps()) <= CRM_SITE_APPS:
		return False
	return has_prefilled_settings() and has_non_admin_user() and is_fc_site()


def has_prefilled_settings():
	settings = frappe.get_single("System Settings")
	return bool(settings.country and settings.time_zone and settings.currency)


def get_prefilled_setup_args():
	settings = frappe.get_single("System Settings")
	language = frappe.db.get_value("Language", settings.language, "language_name") or "English"
	return {
		"language": language,
		"lang": language,
		"country": settings.country,
		"timezone": settings.time_zone,
		"currency": settings.currency,
	}


@frappe.whitelist()
def get_first_lead():
	lead = frappe.get_all(
		"CRM Lead",
		filters={"converted": 0},
		fields=["name"],
		order_by="creation",
		limit=1,
	)
	return lead[0].name if lead else None


@frappe.whitelist()
def get_first_deal():
	deal = frappe.get_all(
		"CRM Deal",
		fields=["name"],
		order_by="creation",
		limit=1,
	)
	return deal[0].name if deal else None
