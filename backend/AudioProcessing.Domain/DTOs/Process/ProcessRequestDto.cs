using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AudioProcessing.Domain.DTOs.Process;

public class ProcessRequestDto
{
    public Guid TrackId { get; set; }
    public MusicGenre Genre { get; set; }
    public MusicInstrument Instrument { get; set; }
}

public enum MusicGenre
{
    Classic,
    Jazz,
    Rock
}

public enum MusicInstrument
{
    Guitar,
    Piano,
    Vocal
}