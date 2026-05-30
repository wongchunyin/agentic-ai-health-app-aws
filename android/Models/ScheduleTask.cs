using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LiveWell.Models
{
    public class ScheduleTask
    {
        public string plan_id { get; set; }
        public int cnt_activity_done { get; set; }
        public int target { get; set; }
    }
}
