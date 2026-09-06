import React, {useEffect, useState} from 'react';
import {useParams} from 'react-router-dom';
import {fetchCountryDetails} from '../services/api.js';
import CountryDetail from "../components/CountryDetail.jsx";

const Detail = () => {
    const {countryName} = useParams();
    const [country, setCountry] = useState(null);

    useEffect(() => {
        const getCountryDetails = async () => {
            const data = await fetchCountryDetails(countryName);
            setCountry(data);
        };
        getCountryDetails();
    }, [countryName]);


    if (!country) return <div>Loading...</div>;

    return (
        <CountryDetail country={country}/>
    );
};

export default Detail;