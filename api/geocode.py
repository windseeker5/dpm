# api/geocode.py - Location Geocoding Service
from flask import Blueprint, request, jsonify
import requests
import os
import time

geocode_api = Blueprint('geocode_api', __name__, url_prefix='/api')

# ============================================================================
# GEOCODING OPERATIONS
# ============================================================================

@geocode_api.route('/geocode', methods=['POST'])
def geocode_address():
    """
    Geocode an address using Google Maps API or Nominatim (OpenStreetMap)

    Request JSON:
    {
        "address": "Complexe Desjardins, Montreal"
    }

    Response JSON:
    {
        "success": true,
        "formatted_address": "Complexe Desjardins, 150 Rue Sainte-Catherine O...",
        "coordinates": "45.508384,-73.567750",
        "error": null
    }
    """
    try:
        data = request.get_json()
        address = data.get('address', '').strip()

        if not address:
            return jsonify({
                'success': False,
                'error': 'Address is required'
            }), 400

        # Try Google Maps API first (if key available)
        google_api_key = os.getenv('GOOGLE_MAPS_API_KEY')

        if google_api_key:
            result = geocode_with_google(address, google_api_key)
            if result['success']:
                return jsonify(result), 200

        # Fallback to Nominatim (free, no API key required)
        result = geocode_with_nominatim(address)
        return jsonify(result), 200 if result['success'] else 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Geocoding service error: {str(e)}'
        }), 500


def geocode_with_google(address, api_key):
    """
    Geocode using Google Maps Geocoding API
    Docs: https://developers.google.com/maps/documentation/geocoding
    """
    try:
        url = 'https://maps.googleapis.com/maps/api/geocode/json'
        params = {
            'address': address,
            'key': api_key,
            'region': 'ca'  # Bias results to Canada
        }

        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        if data['status'] == 'OK' and data['results']:
            result = data['results'][0]
            location = result['geometry']['location']

            return {
                'success': True,
                'formatted_address': result['formatted_address'],
                'coordinates': f"{location['lat']},{location['lng']}",
                'provider': 'google',
                'error': None
            }
        else:
            return {
                'success': False,
                'error': f"Google Maps error: {data.get('status', 'Unknown error')}"
            }

    except Exception as e:
        return {
            'success': False,
            'error': f'Google Maps API error: {str(e)}'
        }


def geocode_with_nominatim(address):
    """
    Geocode using Nominatim (OpenStreetMap) - Free, no API key required
    Docs: https://nominatim.org/release-docs/develop/api/Search/

    Note: Rate limited to 1 request per second
    """
    try:
        url = 'https://nominatim.openstreetmap.org/search'
        params = {
            'q': address,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1,
            'countrycodes': 'ca'  # Bias to Canada
        }

        headers = {
            'User-Agent': 'MiniPass Activity Manager/1.0'  # Required by Nominatim
        }

        response = requests.get(url, params=params, headers=headers, timeout=5)
        data = response.json()

        if data and len(data) > 0:
            result = data[0]

            # Build formatted address from components
            addr_parts = []
            address_details = result.get('address', {})

            # Add building/amenity name if available
            if 'amenity' in address_details:
                addr_parts.append(address_details['amenity'])
            elif 'building' in address_details:
                addr_parts.append(address_details['building'])

            # Add street address
            if 'house_number' in address_details and 'road' in address_details:
                addr_parts.append(f"{address_details['house_number']} {address_details['road']}")
            elif 'road' in address_details:
                addr_parts.append(address_details['road'])

            # Add city
            city = address_details.get('city') or address_details.get('town') or address_details.get('village')
            if city:
                addr_parts.append(city)

            # Add province
            if 'state' in address_details:
                addr_parts.append(address_details['state'])

            # Add postal code if available
            if 'postcode' in address_details:
                addr_parts.append(address_details['postcode'])

            formatted_address = ', '.join(addr_parts) if addr_parts else result.get('display_name', address)

            return {
                'success': True,
                'formatted_address': formatted_address,
                'coordinates': f"{result['lat']},{result['lon']}",
                'provider': 'nominatim',
                'error': None
            }
        else:
            return {
                'success': False,
                'error': 'Location not found. Please check the address and try again.'
            }

    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'Geocoding service timeout. Please try again.'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Nominatim API error: {str(e)}'
        }
