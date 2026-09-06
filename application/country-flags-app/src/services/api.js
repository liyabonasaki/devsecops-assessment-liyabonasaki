import axios from "axios";

const API_URL = `${process.env.REACT_APP_API_URL}/api/countries` || 'http://localhost:8081/api/countries';

export const fetchAllCountries = async () => {
    try {
        const response = await axios.get(`${API_URL}`);
        return response.data;
    } catch (error) {
        throw new Error(`Error fetching countries: ${error.message}`);
    }
};

export const fetchCountryDetails = async (countryName) => {
    try {
        const response = await axios.get(`${API_URL}/${countryName}`);
        return response.data;
    } catch (error) {
        throw new Error(`Error fetching country details: ${error.message}`);
    }
};