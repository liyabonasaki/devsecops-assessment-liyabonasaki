package org.bongz.countryservice.service;

import org.bongz.countryservice.dto.CountryDTO;
import org.bongz.countryservice.dto.CountryDetailsDTO;
import org.bongz.countryservice.model.Country;
import org.bongz.countryservice.repository.CountryRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

import java.util.Arrays;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.when;

public class CountryServiceTest {

    @Mock
    private CountryRepository countryRepository;

    @InjectMocks
    private CountryService countryService;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    @Test
    void serviceShouldReturnAllCountries() {
        List<Country> mockedCountries = Arrays.asList(
                new Country("Nigeria", "🇳🇬"),
                new Country("Egypt", "🇪🇬")
        );

        when(countryRepository.findAll()).thenReturn(mockedCountries);

        List<CountryDTO> countries = countryService.getAllCountries();

        assertEquals(2, countries.size());
        assertEquals("Nigeria", countries.get(0).name());
        assertEquals("Egypt", countries.get(1).name());
    }

    @Test
    void serviceShouldGetCountryDetails() {
        String countryName = "Egypt";
        String countryCapital = "Cairo";
        Country mockCountry = new Country(countryName, "🇪🇬", 97_000_000, countryCapital);

        when(countryRepository.findByNameIgnoreCase(countryName)).thenReturn(mockCountry);

        // Test
        Optional<CountryDetailsDTO> details = countryService.getCountryDetails(countryName);

        // Verify
        assertTrue(details.isPresent());
        assertEquals(countryName, details.get().name());
        assertEquals(countryCapital, details.get().capital());

    }

    @Test
    void serviceShouldGetEmptyCountryDetailsGivenCountryDoesNotExist() {
        String countryName = "abc";

        when(countryRepository.findByNameIgnoreCase(countryName)).thenReturn(null);

        // Test
        Optional<CountryDetailsDTO> details = countryService.getCountryDetails(countryName);

        // Verify
        assertTrue(details.isEmpty());

    }

}
