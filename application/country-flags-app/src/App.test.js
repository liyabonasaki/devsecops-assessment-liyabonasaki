import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from './App';

jest.mock('./pages/Home', () => () => <div>Home Page</div>);
jest.mock('./pages/Detail', () => () => <div>Detail Page</div>);

describe('App Component', () => {
    test('renders Home page by default', () => {
        render(
            <MemoryRouter initialEntries={['/']}>
                <App />
            </MemoryRouter>
        );
        expect(screen.getByText('Home Page')).toBeInTheDocument();
    });

    test('renders Detail page when navigating to /detail/country', () => {
        render(
            <MemoryRouter initialEntries={['/detail/country']}>
                <App />
            </MemoryRouter>
        );
        expect(screen.getByText('Detail Page')).toBeInTheDocument();
    });

    test('renders 404 message for an unknown route', () => {
        render(
            <MemoryRouter initialEntries={['/unknown-route']}>
                <App />
            </MemoryRouter>
        );
        expect(screen.getByText('Page Not Found')).toBeInTheDocument();
    });
});
