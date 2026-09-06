package org.bongz.countryservice;

import org.bongz.countryservice.model.Country;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.web.client.RestTemplate;

import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;

@SpringBootTest
@ActiveProfiles("test")
class CountryServiceApplicationTests {

    @MockBean
    private RestTemplate restTemplate; // Mock the RestTemplate

    @Test
    void contextLoads() {
        // Mock the API response
        when(restTemplate.getForObject(anyString(), eq(Country[].class)))
                .thenReturn(new Country[0]); // Return an empty array

    }

}
