using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Configuration;
using System.Net.Http;
using System.Threading.Tasks;
using Microservice1.Data;  // Для AppDbContext
using Microservice1.Models; // Для RequestData

namespace Microservice1.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class DataController : ControllerBase
    {
        private readonly AppDbContext _context;
        private readonly HttpClient _httpClient;
        private readonly string _pythonServiceUrl;

        public DataController(AppDbContext context, IConfiguration config)
        {
            _context = context;
            _pythonServiceUrl = config["PythonServiceUrl"];
            _httpClient = new HttpClient();
        }

        [HttpPost]
        public async Task<IActionResult> Post([FromBody] RequestData data)
        {
            // Валидация данных
            if (string.IsNullOrEmpty(data.Name))
                return BadRequest("Name is required");
            
            if (string.IsNullOrEmpty(data.Email))
                return BadRequest("Email is required");

            // Сохранение в основную таблицу
            _context.RequestData.Add(data);
            await _context.SaveChangesAsync();

            // Отправка в Python-микросервис
            var response = await _httpClient.PostAsJsonAsync(
                $"{_pythonServiceUrl}/api/process", 
                new { 
                    data.Name, 
                    data.Email,
                    source = "C# service"
                });

            if (!response.IsSuccessStatusCode)
            {
                return StatusCode(500, "Error processing data in Python service");
            }

            return Ok(new { 
                Message = "Data saved and processed",
                Id = data.Id,
                PythonResponse = await response.Content.ReadFromJsonAsync<object>()
            });
        }
    }
}