import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter as Router } from 'react-router-dom';  // Import BrowserRouter
import CountryDetail from './CountryDetail.jsx';

// Mock react-router-dom
jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: jest.fn(() => ({ countryName: '123' })),
    useNavigate: jest.fn(),
}));

const mockNavigate = jest.fn();

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: () => mockNavigate,
}));

const mockCountry = {
    name: 'United States' ,
    population: 331002651,
    capital: 'Washington, D.C.',
    flag: 'https://flagcdn.com/us.png' ,
};

describe('CountryDetail Component', () => {
    it('renders country details correctly', () => {
        render(
            <Router>  {/* Wrap with Router */}
                <CountryDetail country={mockCountry} />
            </Router>
        );

        expect(screen.getByText('United States')).toBeInTheDocument();
        expect(screen.getByText((content, element) => {
            return element.textContent === 'Population: 331,002,651';
        })).toBeInTheDocument();
        expect(screen.getByText((content, element) => {
            return element.textContent === 'Capital: Washington, D.C.';
        })).toBeInTheDocument();
    });

    it('renders the flag image', () => {
        render(
            <Router> {/* Wrap with Router */}
                <CountryDetail country={mockCountry} />
            </Router>
        );

        const flagImage = screen.getByAltText('United States');
        expect(flagImage).toBeInTheDocument();
        expect(flagImage.src).toBe('https://flagcdn.com/us.png');
    });

    it('navigates back to home when back button is clicked', () => {
        render(
            <Router>
                <CountryDetail country={mockCountry} />
            </Router>
        );

        const backButton = screen.getByText('Back to Home');
        fireEvent.click(backButton);

        expect(mockNavigate).toHaveBeenCalledWith('/');
    });
});
