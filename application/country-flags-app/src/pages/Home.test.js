import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter as Router } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import Home from './Home.jsx';
import { fetchAllCountries } from '../services/api.js';

// Mock the API module
jest.mock('../services/api.js');

const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: () => mockNavigate,
}));

/* eslint-disable testing-library/no-wait-for-multiple-assertions */

describe('Home Component', () => {
    const mockCountries = [
        {
            name: 'United States' ,
            flag: 'https://flagcdn.com/us.png' ,
        },
        {
            name: 'India',
            flag: 'https://flagcdn.com/in.png' ,
        },
    ];

    beforeEach(() => {
        // Mock the API response
        fetchAllCountries.mockResolvedValue(mockCountries);
    });

    it('renders the home page with country flags', async () => {
        render(
            <Router>
                <Home />
            </Router>
        );

        // Check if the heading is rendered
        expect(screen.getByText('Country Flags')).toBeInTheDocument();

        // Wait for the data to load and check if flags are rendered
        await waitFor(() => {
            expect(screen.getByText('United States')).toBeInTheDocument();
            expect(screen.getByText('India')).toBeInTheDocument();
        });
    });

    it('calls fetchAllCountries on mount', async () => {
        render(
            <Router>
                <Home />
            </Router>
        );

        // Check if the API was called
        await waitFor(() => {
            expect(fetchAllCountries).toHaveBeenCalledTimes(1);
        });
    });

    it('navigates to country detail page when a flag is clicked', async () => {
        const mockCountries = [
            { name: 'United States', flag: 'https://flagcdn.com/us.png' },
        ];

        fetchAllCountries.mockResolvedValue(mockCountries);

        render(
            <Router>
                <Home />
            </Router>
        );

        // eslint-disable-next-line testing-library/no-wait-for-multiple-assertions
        await waitFor(() => {
            expect(screen.getByAltText('United States')).toBeInTheDocument();
        });

        // Simulate user clicking on the United States flag
        userEvent.click(screen.getByAltText('United States'));

        // Expect navigation to be called with the correct route
        expect(mockNavigate).toHaveBeenCalledWith('/detail/United States');
    });
});