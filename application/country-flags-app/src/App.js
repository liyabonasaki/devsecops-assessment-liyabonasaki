import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Home from './pages/Home.jsx';
import Detail from './pages/Detail.jsx';

const App = () => {
    return (
        <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/detail/:countryName" element={<Detail />} />
            <Route path="*" element={<div>Page Not Found</div>} />
        </Routes>
    );
};

export default App;
