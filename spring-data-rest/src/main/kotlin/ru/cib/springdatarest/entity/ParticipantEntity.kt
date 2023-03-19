package ru.cib.springdatarest.entity

import jakarta.persistence.Entity
import jakarta.persistence.GeneratedValue
import jakarta.persistence.Id
import jakarta.persistence.ManyToOne
import jakarta.persistence.Table

@Entity
@Table(name = "_participant")
data class ParticipantEntity(
    @Id
    @GeneratedValue
    var id: Int? = null,
    var firstName: String? = null,
    var lastName: String? = null,
    var age: Int? = null,
    var programmingLanguage: String? = null,
    @ManyToOne
    var team: TeamEntity? = null,
)