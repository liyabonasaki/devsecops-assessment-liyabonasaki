package org.bongz.countryservice.dto;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "Basic country details")
public record CountryDTO(
        @Schema(description = "Name of the country", example = "South Africa") String name,
        @Schema(description = "Flag URL", example = "https://flagcdn.com/za.svg") String flag
) {

}
