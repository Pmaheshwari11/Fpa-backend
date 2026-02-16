def calculate_expected_value(probability, opportunity_value):

    return probability * opportunity_value


def calculate_forecast(metrics):

    contacts = metrics.get("contacts_added", 0)

    responses = metrics.get("responses", 0)

    interviews = metrics.get("interviews", 0)

    offers = metrics.get("offers", 0)

    response_rate = responses / contacts if contacts else 0

    interview_rate = interviews / responses if responses else 0

    offer_rate = offers / interviews if interviews else 0

    forecast_offers = contacts * response_rate * interview_rate * offer_rate

    return {

        "response_rate": response_rate,

        "interview_rate": interview_rate,

        "offer_rate": offer_rate,

        "forecast_offers": forecast_offers

    }

