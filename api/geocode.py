# api/geocode.py - Location Geocoding Service
from flask import Blueprint, request, jsonify
import requests
import os
import time

geocode_api = Blueprint('geocode_api', __name__, url_prefix='/api')

# ============================================================================
# PLACES AUTOCOMPLETE (for partial address matching)
# ============================================================================

@geocode_api.route('/places/autocomplete', methods=['POST'])
def places_autocomplete():
    """
    Get address suggestions using Google Places Autocomplete API.
    This is designed for partial address matching (e.g., "821 rue des").

    Request JSON:
    {
        "input": "821 rue des"
    }

    Response JSON:
    {
        "success": true,
        "results": [
            {"description": "821 Rue des Sables, Rimouski, QC, Canada", "place_id": "..."},
            {"description": "821 Rue des Sapins, Saint-Eustache, QC, Canada", "place_id": "..."}
        ]
    }
    """
    try:
        data = request.get_json()
        input_text = data.get('input', '').strip()

        if not input_text:
            return jsonify({'success': False, 'error': 'Input is required'}), 400

        google_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not google_api_key:
            return jsonify({'success': False, 'error': 'Google API key not configured'}), 500

        # Call Google Places Autocomplete API
        url = 'https://maps.googleapis.com/maps/api/place/autocomplete/json'
        params = {
            'input': input_text,
            'key': google_api_key,
            'components': 'country:ca'  # Restrict to Canada (no types restriction - returns all places)
        }

        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        if data['status'] == 'OK' and data.get('predictions'):
            results = []
            for pred in data['predictions'][:5]:
                results.append({
                    'description': pred['description'],
                    'place_id': pred['place_id']
                })
            return jsonify({'success': True, 'results': results}), 200
        elif data['status'] == 'ZERO_RESULTS':
            return jsonify({'success': True, 'results': []}), 200
        else:
            return jsonify({'success': False, 'error': f"Google API error: {data.get('status')}"}), 400

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@geocode_api.route('/places/details', methods=['POST'])
def places_details():
    """
    Get full address details (including coordinates) for a place_id.

    Request JSON:
    {
        "place_id": "ChIJ..."
    }

    Response JSON:
    {
        "success": true,
        "formatted_address": "821 Rue des Sables, Rimouski, QC G5L 6Y7, Canada",
        "coordinates": "48.4310142,-68.5923085"
    }
    """
    try:
        data = request.get_json()
        place_id = data.get('place_id', '').strip()

        if not place_id:
            return jsonify({'success': False, 'error': 'place_id is required'}), 400

        google_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not google_api_key:
            return jsonify({'success': False, 'error': 'Google API key not configured'}), 500

        # Call Google Places Details API
        url = 'https://maps.googleapis.com/maps/api/place/details/json'
        params = {
            'place_id': place_id,
            'key': google_api_key,
            'fields': 'formatted_address,geometry'
        }

        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        if data['status'] == 'OK' and data.get('result'):
            result = data['result']
            location = result['geometry']['location']
            return jsonify({
                'success': True,
                'formatted_address': result['formatted_address'],
                'coordinates': f"{location['lat']},{location['lng']}"
            }), 200
        else:
            return jsonify({'success': False, 'error': f"Google API error: {data.get('status')}"}), 400

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


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
    Returns up to 5 results for user selection.
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
            # Return up to 5 results for user selection
            results = []
            for result in data['results'][:5]:
                location = result['geometry']['location']
                results.append({
                    'formatted_address': result['formatted_address'],
                    'coordinates': f"{location['lat']},{location['lng']}"
                })

            return {
                'success': True,
                'results': results,
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
    Returns up to 5 results for user selection.

    Note: Rate limited to 1 request per second
    """
    try:
        url = 'https://nominatim.openstreetmap.org/search'
        params = {
            'q': address,
            'format': 'json',
            'limit': 5,  # Return up to 5 results for user selection
            'addressdetails': 1,
            'countrycodes': 'ca'  # Bias to Canada
        }

        headers = {
            'User-Agent': 'MiniPass Activity Manager/1.0'  # Required by Nominatim
        }

        response = requests.get(url, params=params, headers=headers, timeout=5)
        data = response.json()

        if data and len(data) > 0:
            results = []
            for item in data:
                # Build formatted address from components
                addr_parts = []
                address_details = item.get('address', {})

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

                formatted_address = ', '.join(addr_parts) if addr_parts else item.get('display_name', address)

                results.append({
                    'formatted_address': formatted_address,
                    'coordinates': f"{item['lat']},{item['lon']}"
                })

            return {
                'success': True,
                'results': results,
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
