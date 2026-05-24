from .sop import SOP


def answer_from_sop(message: str, sop: SOP) -> tuple[str | None, str]:
    lowered = message.lower()
    service = sop.service_by_name(message)

    if any(word in lowered for word in ("book", "appointment", "schedule")):
        policy = sop.data["booking"]["cancellation_policy"]
        return (
            f"You can book via {sop.booking_channels()}. The SOP says {policy}.",
            "booking",
        )

    if service and any(word in lowered for word in ("price", "cost", "much", "fee")):
        return (
            f"{service['name']} pricing starts {service['price']} at {sop.business}.",
            "service_pricing",
        )

    if service:
        return (
            f"{sop.business} offers {service['name']}. Pricing listed in the SOP is {service['price']}.",
            "service_information",
        )

    if any(word in lowered for word in ("hour", "open", "close", "time")):
        return f"{sop.business} is open {sop.data['hours']}.", "hours"

    if "cancel" in lowered:
        return sop.data["booking"]["cancellation_policy"].capitalize() + ".", "cancellation"

    return None, "out_of_scope"
