package org.bongz.countryservice.dto;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "Detailed country information")
public record CountryDetailsDTO(
        @Schema(description = "Name of the country", example = "South Africa") String name,
        @Schema(description = "Population of the country", example = "60000000") int population,
        @Schema(description = "Capital city", example = "Pretoria") String capital,
        @Schema(description = "Flag URL", example = "https://flagcdn.com/za.svg") String flag
) {
}
