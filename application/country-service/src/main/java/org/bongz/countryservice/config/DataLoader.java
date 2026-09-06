package org.bongz.countryservice.config;

import org.bongz.countryservice.model.ApiCountry;
import org.bongz.countryservice.model.Country;
import org.bongz.countryservice.repository.CountryRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.util.Arrays;
import java.util.Optional;

@Profile("dev") // Disable this component during tests
@Component
public class DataLoader implements ApplicationRunner {

    private static final Logger logger = LoggerFactory.getLogger(DataLoader.class);

    private final CountryRepository countryRepository;
    private final RestTemplate restTemplate;

    public DataLoader(CountryRepository countryRepository, RestTemplate restTemplate) {
        this.countryRepository = countryRepository;
        this.restTemplate = restTemplate;
    }

    @Override
    public void run(ApplicationArguments args) throws Exception {
        try {
            // Fetch data from the external API
            ApiCountry[] apiCountries = restTemplate.getForObject("https://restcountries.com/v3.1/all", ApiCountry[].class);

            if (apiCountries != null) {
                // Save data to the database
                Arrays.stream(apiCountries).forEach(apiCountry -> {
                    try {
                        // Extract the "common" name and the first capital
                        String name = Optional.ofNullable(apiCountry.getName())
                                .map(ApiCountry.Name::getCommon)
                                .orElse("N/A");

                        // Extract the PNG flag URL from the "flags" object
                        String flag = Optional.ofNullable(apiCountry.getFlags())
                                .map(ApiCountry.Flags::getPng)
                                .orElse("N/A");

                        String capital = Optional.ofNullable(apiCountry.getCapital())
                                .filter(caps -> !caps.isEmpty())
                                .map(caps -> caps.get(0))
                                .orElse("N/A");

                        // Create a simplified Country object
                        Country country = new Country(
                                name, // Simplified: Directly use the "common" name
                                flag,
                                apiCountry.getPopulation(),
                                capital // Simplified: Use only the first capital
                        );

                        // Save the country to the database
                        countryRepository.save(country);
                        logger.info("Saved country: {}", name);
                    } catch (Exception e) {
                        logger.error("Error processing country data: {}", apiCountry, e);
                    }
                });
            } else {
                logger.warn("No countries fetched from the API.");
            }
        } catch (Exception e) {
            logger.error("Error fetching data from the API", e);
        }
    }
}