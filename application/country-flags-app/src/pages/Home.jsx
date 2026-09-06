import React, { useEffect, useState } from 'react';
import { fetchAllCountries } from '../services/api.js';
import FlagGrid from '../components/FlagGrid.jsx';
import { useNavigate } from 'react-router-dom';

const Home = () => {
    const [countries, setCountries] = useState([]);
    const navigate = useNavigate();

    useEffect(() => {
        const getCountries = async () => {
            const data = await fetchAllCountries();
            setCountries(data);
        };
        getCountries();
    }, []);

    const handleFlagClick = (countryName) => {
        navigate(`/detail/${countryName}`);
    };

    return (
        <div>
            <h1>Country Flags</h1>
            <FlagGrid countries={countries} onFlagClick={handleFlagClick} />
        </div>
    );
};

export default Home;