using Microsoft.EntityFrameworkCore;
using Microservice1.Models;

namespace Microservice1.Data;

public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

    public DbSet<RequestData> RequestData { get; set; }
}