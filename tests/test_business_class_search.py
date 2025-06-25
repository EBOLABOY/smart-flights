import pytest
import asyncio
from fli.api.kiwi_oneway import KiwiOnewayAPI

@pytest.mark.asyncio
async def test_lhr_pek_business_search():
    """
    Tests a one-way business class search from LHR to PEK.
    """
    api = KiwiOnewayAPI(cabin_class="BUSINESS")
    
    # The main purpose is to ensure the search call can be made without errors.
    # A full response validation is not required for this test.
    result = await api.search_hidden_city_flights(
        origin="LHR",
        destination="PEK",
        departure_date="2025-06-30"
    )
    
    print("API call executed. Checking for basic response structure.")
    assert result is not None, "API response should not be None"
    assert isinstance(result, dict), "The result should be a dictionary"
    assert result.get("success") is True, "The search should be successful"
    print("Test passed: Business class search API call was successful.")
@pytest.mark.asyncio
async def test_hidden_city_only_filter():
    """
    Tests that the hidden_city_only=True flag correctly filters results
    to only include hidden city flights.
    """
    api = KiwiOnewayAPI(cabin_class="BUSINESS", hidden_city_only=True)
    
    result = await api.search_hidden_city_flights(
        origin="LHR",
        destination="PEK",
        departure_date="2025-06-30"
    )
    
    assert result is not None, "API response should not be None"
    assert result.get("success") is True, "The search should be successful"
    
    flights = result.get("results", {}).get("flights", [])
    
    # If there are flights, they should all be hidden city flights
    if flights:
        for flight in flights:
            assert flight.get("is_hidden_city") is True, \
                f"Flight {flight.get('id')} should be a hidden city flight, but it is not."
    
    print("Test passed: hidden_city_only filter works as expected.")