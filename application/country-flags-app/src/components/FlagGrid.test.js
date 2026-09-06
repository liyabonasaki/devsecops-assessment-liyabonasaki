import React from 'react';
import { render, screen } from '@testing-library/react';
import FlagGrid from './FlagGrid';

const mockCountries = [
    {
        name: 'United States',
        flag: 'https://flagcdn.com/us.png' ,
    },
    {
        name: 'India',
        flag: 'https://flagcdn.com/in.png',
    },
];

describe('FlagGrid Component', () => {
    it('renders all country flags', () => {
        render(<FlagGrid countries={mockCountries} onFlagClick={() => {}} />);

        // Check if all flags are rendered
        expect(screen.getByText('United States')).toBeInTheDocument();
        expect(screen.getByText('India')).toBeInTheDocument();
    });

    it('calls onFlagClick when a flag is clicked', () => {
        const mockOnClick = jest.fn();
        render(<FlagGrid countries={mockCountries} onFlagClick={mockOnClick} />);

        // Simulate clicking the first flag
        screen.getByText('United States').click();
        expect(mockOnClick).toHaveBeenCalledWith('United States');
    });
});