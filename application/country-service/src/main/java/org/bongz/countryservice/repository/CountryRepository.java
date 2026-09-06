package org.bongz.countryservice.repository;

import org.bongz.countryservice.model.Country;
import org.springframework.data.jpa.repository.JpaRepository;


public interface CountryRepository extends JpaRepository<Country, Long> {
    Country findByNameIgnoreCase(String egypt);
}
