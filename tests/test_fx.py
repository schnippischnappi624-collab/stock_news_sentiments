from stock_news.fx import convert_to_eur, parse_ecb_rates_xml, select_eur_rates


def test_parse_and_select_ecb_rates_by_target_date() -> None:
    xml_payload = """
    <gesmes:Envelope xmlns:gesmes="http://www.gesmes.org/xml/2002-08-01" xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref">
      <Cube>
        <Cube time="2026-04-10">
          <Cube currency="USD" rate="2.0"/>
          <Cube currency="NOK" rate="10.0"/>
        </Cube>
        <Cube time="2026-04-11">
          <Cube currency="USD" rate="2.2"/>
          <Cube currency="NOK" rate="11.0"/>
        </Cube>
      </Cube>
    </gesmes:Envelope>
    """

    payload = parse_ecb_rates_xml(xml_payload)
    selected = select_eur_rates(payload, target_date="2026-04-10")

    assert selected["rate_date"] == "2026-04-10"
    assert selected["rates"]["USD"] == 2.0
    assert selected["rates"]["NOK"] == 10.0


def test_convert_to_eur_uses_selected_rate_table() -> None:
    context = {"rate_date": "2026-04-10", "rates": {"EUR": 1.0, "USD": 2.0, "NOK": 10.0}}

    assert convert_to_eur(20.0, "USD", context) == 10.0
    assert convert_to_eur(110.0, "NOK", context) == 11.0
    assert convert_to_eur(15.0, "EUR", context) == 15.0
    assert convert_to_eur(15.0, "CHF", context) is None
