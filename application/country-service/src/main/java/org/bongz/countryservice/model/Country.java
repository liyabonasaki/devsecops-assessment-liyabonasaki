package org.bongz.countryservice.model;


import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Table;
import jakarta.persistence.Id;

@Entity
@Table(name = "countries")
public class Country {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String name; // Simplified: Directly store the "common" name
    private String flag;
    private int population;
    private String capital; // Simplified: Store only the first capital

    // Constructor for basic fields

    public Country() {
    }

    public Country(String name, String flag) {
        this.name = name;
        this.flag = flag;
    }

    // Constructor for all fields
    public Country(String name, String flag, int population, String capital) {
        this.name = name;
        this.flag = flag;
        this.population = population;
        this.capital = capital;
    }

    public String getName() {
        return name;
    }

    public String getFlag() {
        return flag;
    }

    public int getPopulation() {
        return population;
    }

    public String getCapital() {
        return capital;
    }
}