import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter as Router } from 'react-router-dom';
import Detail from './Detail.jsx';
import { fetchCountryDetails } from '../services/api.js';

// Mock API service
jest.mock('../services/api.js');

// Mock useParams from react-router-dom
jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({ countryName: 'United States' }),
}));

/* eslint-disable testing-library/no-wait-for-multiple-assertions */
describe('Detail Page', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('renders loading state initially', () => {
        fetchCountryDetails.mockResolvedValueOnce(null);

        render(
            <Router>
                <Detail />
            </Router>
        );

        expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });

    it('renders country details after fetching data', async () => {
        const mockCountry = {
            name: 'United States',
            population: 331002651,
            capital: 'Washington, D.C.',
            flag: 'https://flagcdn.com/us.png',
        };

        fetchCountryDetails.mockResolvedValueOnce(mockCountry);

        render(
            <Router>
                <Detail />
            </Router>
        );

        // Wait for data to load
        await waitFor(() => {
            expect(screen.getByText('United States')).toBeInTheDocument();
        });

        // Verify elements exist using more robust matchers
        expect(screen.getByText(/Population:/i)).toBeInTheDocument();
        expect(screen.getByText(/331,002,651/i)).toBeInTheDocument();
        expect(screen.getByText(/Capital:/i)).toBeInTheDocument();
        expect(screen.getByText(/Washington, D\.C\./i)).toBeInTheDocument();

        // Ensure flag image is displayed
        const flagImage = screen.getByAltText(/United States/i);
        expect(flagImage).toBeInTheDocument();
        expect(flagImage.src).toBe(mockCountry.flag);
    });

    it('calls fetchCountryDetails with correct params', async () => {
        const mockCountry = {
            name: 'United States',
            population: 331002651,
            capital: 'Washington, D.C.',
            flag: 'https://flagcdn.com/us.png',
        };

        fetchCountryDetails.mockResolvedValueOnce(mockCountry);

        render(
            <Router>
                <Detail />
            </Router>
        );

        await waitFor(() => {
            expect(fetchCountryDetails).toHaveBeenCalledTimes(1);
            expect(fetchCountryDetails).toHaveBeenCalledWith('United States');
        });
    });
});
