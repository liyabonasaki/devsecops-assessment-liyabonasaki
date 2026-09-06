import React from 'react';
import { Grid, Card, CardMedia, CardContent, Typography } from '@mui/material';

const FlagGrid = ({ countries, onFlagClick }) => {
    return (
        <Grid container spacing={3} style={{ padding: '20px' }}>
            {countries.map((country, idx) => (
                <Grid item key={idx} xs={12} sm={6} md={4} lg={3}>
                    <Card onClick={() => onFlagClick(country.name)} style={{ cursor: 'pointer' }}>
                        <CardMedia
                            component="img"
                            height="150"
                            image={country.flag}
                            alt={country.name}
                            style={{
                                objectFit: 'contain',
                            }}
                        />
                        <CardContent>
                            <Typography variant="h6" align="center">
                                {country.name}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
            ))}
        </Grid>
    );
};

export default FlagGrid;