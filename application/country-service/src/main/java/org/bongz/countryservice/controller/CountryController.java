package org.bongz.countryservice.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.bongz.countryservice.dto.CountryDTO;
import org.bongz.countryservice.dto.CountryDetailsDTO;
import org.bongz.countryservice.service.CountryService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Optional;

@RestController
@RequestMapping("/api/countries")
@Tag(name = "Country API", description = "API for retrieving country information")
public class CountryController {

    private final CountryService countryService;

    public CountryController(CountryService countryService) {
        this.countryService = countryService;
    }

    @Operation(
            summary = "Retrieve all countries",
            description = "Returns a list of all available countries",
            responses = {@ApiResponse(responseCode = "200", description = "A list of countries", content = @Content(mediaType = "application/json",
                    schema = @Schema(implementation = CountryDTO.class)))}
    )
    @GetMapping
    public List<CountryDTO> getAllCountries() {
        return countryService.getAllCountries();
    }

    @Operation(
            summary = "Retrieve details about a specific country",
            description = "Provide a country name to look up its details",
            responses = { @ApiResponse(responseCode = "200", description = "Details about the country",
                            content = @Content(mediaType = "application/json",
                                    schema = @Schema(implementation = CountryDetailsDTO.class))), @ApiResponse(responseCode = "404", description = "Country not found")
            }
    )
    @GetMapping("/{countryName}")
    public ResponseEntity<?> getCountry(
            @Parameter(description = "Name of the country", required = true)
            @PathVariable String countryName) {
        Optional<CountryDetailsDTO> country = countryService.getCountryDetails(countryName);
        return country.map(ResponseEntity::ok).orElse(ResponseEntity.notFound().build());
    }
}
