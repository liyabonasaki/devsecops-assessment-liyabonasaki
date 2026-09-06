const axios = require('axios');
const MockAdapter = require('axios-mock-adapter');
const {fetchAllCountries, fetchCountryDetails} = require("./api.js");

// Create a mock instance of axios
const mock = new MockAdapter(axios);

// Mock the environment variable
const API_URL = "http://localhost:8081/api/countries"; // Mocked API URL

describe('API Service', () => {
    afterEach(() => {
        mock.reset(); // Reset the mock after each test
    });

    // Test for fetchAllCountries
    describe('fetchAllCountries', () => {
        it('should fetch all countries successfully', async () => {
            const mockData = [
                { name: 'South Georgia' , flag: 'https://flagcdn.com/sg.png' },
                { name: 'Tunisia' , flag: 'https://flagcdn.com/tunisia.png' },
            ];

            // Mock the GET request to return the mockData
            mock.onGet(`${API_URL}`).reply(200, mockData);

            const result = await fetchAllCountries();

            expect(result).toEqual(mockData); // Assert that the result matches the mockData
            expect(mock.history.get.length).toBe(1); // Assert that the API was called once
        });

        it('should handle errors when fetching all countries', async () => {
            // Mock the GET request to return an error
            mock.onGet(`${API_URL}`).reply(500, 'Server Error');

            await expect(fetchAllCountries()).rejects.toThrow('Error fetching countries:'); // Assert that an error is thrown
        });

    });

    // Test for fetchCountryDetails
    describe('fetchCountryDetails', () => {
        it('should fetch country details successfully', async () => {
            const mockData =
                {
                    name:'United States',
                    population: 329484123,
                    capital: 'Washington, D.C.',
                    flag: 'https://flagcdn.com/us.png' ,
                };

            // Mock the GET request to return the mockData
            mock.onGet(`${API_URL}/United States`).reply(200, mockData);

            const result = await fetchCountryDetails('United States');

            expect(result).toEqual(mockData); // Assert that the result matches the mockData
            expect(mock.history.get.length).toBe(1); // Assert that the API was called once
        });

        it('should handle errors when fetching country details', async () => {
            // Mock the GET request to return an error
            mock.onGet(`${API_URL}/alpha`).reply(404, 'Not Found');

            await expect(fetchCountryDetails('alpha')).rejects.toThrow("Error fetching country details: Request failed with status code 404");
        });
    });
});