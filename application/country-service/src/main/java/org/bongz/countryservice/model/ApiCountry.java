package org.bongz.countryservice.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.List;

@Data
public class ApiCountry {
    private Name name;
    private Flags flags; // This should map to the "flags" object in the JSON
    private List<String> capital;
    private int population;

    @Data
    public static class Name {
        @JsonProperty("common")
        private String common;

        public String getCommon() {
            return common;
        }
    }

    @Data
    public static class Flags {
        @JsonProperty("png")
        private String png; // Maps to the "png" field in the "flags" object

        @JsonProperty("svg")
        private String svg; // Maps to the "svg" field in the "flags" object

        @JsonProperty("alt")
        private String alt; // Maps to the "alt" field in the "flags" object

        public String getPng() {
            return png;
        }

        public String getSvg() {
            return svg;
        }

        public String getAlt() {
            return alt;
        }
    }

    public Name getName() {
        return name;
    }

    public List<String> getCapital() {
        return capital;
    }

    public Flags getFlags() { // Renamed from getFlag() to getFlags()
        return flags;
    }

    public int getPopulation() {
        return population;
    }
}