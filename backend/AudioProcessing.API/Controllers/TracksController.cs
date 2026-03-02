using AudioProcessing.Domain.Entities.Track;
using AudioProcessing.Infrastructure.Context;
using AudioProcessing.Infrastructure.Storage;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace AudioProcessing.API.Controllers;

[ApiController]
[Route("api/tracks")]
public class TracksController : ControllerBase
{
    private readonly AppDbContext _db;
    private readonly MinioService _minio;

    public TracksController(AppDbContext db, MinioService minio)
    {
        _db = db;
        _minio = minio;
    }

    /// <summary>
    /// Метод сохраняет информацию о треке в базу данных
    /// </summary>
    /// <param name="req"></param>
    /// <returns></returns>
    [HttpPost]
    public async Task<IActionResult> CreateTrack([FromBody] CreateTrackRequest req)
    {
        // проверяем полученные данные
        if (string.IsNullOrWhiteSpace(req.Filename) || string.IsNullOrWhiteSpace(req.StorageKey))
        {
            return BadRequest(new { message = "Filename and StorageKey are required" });
        }

        // проверяем существует ли файл в minio
        bool exists = await _minio.ObjectExistsAsync(req.StorageKey);
        if (!exists)
        {
            return BadRequest("File not found in storage");
        }

        // Проверяем, не создан ли уже Track
        bool alreadyExists = await _db.Tracks.AnyAsync(t => t.StorageKey == req.StorageKey);

        if (alreadyExists)
        {
            return Conflict(new { message = "Track already exists" });
        }

        var track = new TrackEntity
        {
            TrackId = Guid.NewGuid(),
            Filename = req.Filename,
            StorageKey = req.StorageKey,
            CreatedAt = DateTime.UtcNow
        };

        _db.Tracks.Add(track);
        await _db.SaveChangesAsync();

        return CreatedAtAction(
            nameof(GetTrackById),
            new { id = track.TrackId },
            new
            {
                trackId = track.TrackId,
                filename = track.Filename,
                storageKey = track.StorageKey,
                createdAt = track.CreatedAt
            });
    }

    [HttpGet("{id:guid}")]
    public async Task<IActionResult> GetTrackById(Guid id)
    {
        var track = await _db.Tracks.FindAsync(id);
        if (track == null)
            return NotFound();

        return Ok(track);
    }
}