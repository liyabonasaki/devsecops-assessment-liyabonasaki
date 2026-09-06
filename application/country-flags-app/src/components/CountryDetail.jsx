import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, CardMedia, CardContent, Typography, Container } from '@mui/material';

const CountryDetail = ({ country }) => {
    const navigate = useNavigate();

    return (
        <Container style={{ marginTop: '20px' }}>
            <Button
                variant="contained"
                color="primary"
                onClick={() => navigate('/')}
                style={{ marginBottom: '20px' }}
            >
                Back to Home
            </Button>
            <Card>
                <CardMedia
                    component="img"
                    height="250"
                    image={country.flag}
                    alt={country.name}
                    style={{
                        objectFit: 'contain',
                    }}
                />
                <CardContent>
                    <Typography variant="h4" gutterBottom>
                        {country.name}
                    </Typography>
                    <Typography variant="body1" gutterBottom>
                        <strong>Population:</strong> {country.population.toLocaleString()}
                    </Typography>
                    <Typography variant="body1" gutterBottom>
                        <strong>Capital:</strong> {country.capital}
                    </Typography>
                </CardContent>
            </Card>
        </Container>
    );
};

export default CountryDetail;