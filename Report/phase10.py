#!/usr/bin/env python
# coding: utf-8

# <div dir='rtl'>
# <h1>پروژه دهم علوم اعصاب محاسباتی</h1>
# <br/>
# - کد‌ها فقط در ابتدای گزارش زیاد هستند (بخش برپایی آزمایش)
# <br/>
# - گزارش این آزمایش به صورت اینترپرت آماده شده به این معنا که تصمیم بررسی پارامتر بعدی در هر بخش، مستقیما با توجه به نتیجه قسمت قبلی گرفته شده است. درصورت تغییر مقادیر پیش‌فرض برای ادامه‌ی آزمایش پس از یک بخش، این تغییر در پایان آن بخش اعلام خواهد شد.
# <br/>
# - مقادیر پیش‌فرض پس از توده‌ای از آزمایش‌ها قبل از ثبت گزارش تعیین شده‌اند و به نحوی هستند که نتایج قابل قبولی ارائه دهند.
# <br/>
# - با توجه به تصادفی بودن انتخاب‌ها و همچنین Unsupervised بودن آموزش، با اجرای دوباره‌ی هر شبیه‌سازی، تصاویر خروجی جابجا خواهند شد. به همین دلیل، در توضیحات بخش‌ها از اشاره مستقیم به تصاویر خودداری شده است.
# </div>

# <div dir='rtl'>
# <h2>0. فهرست مطالب</h2>
# <ol>
#     <li><a href="#1">دادگان</a></li>
#     <li><a href="#2">برپایی آزمایش</a></li>
#     <li><a href="#3">اجرای آزمایش با مقادیر پیش‌فرض</a></li>
#     <li><a href="#4">اندازه بزرگ کرنل ویژگی</a></li>
#     <li><a href="#5">اندازه کوچک کرنل فیلتر DoG</a></li>
#     <li><a href="#6">مقداردهی اولیه‌ی کرنل ویژگی‌ها</a></li>
#     <ol>
#         <li>بازه انتخاب تصادفی</li>
#         <li>مقدار ثابت</li>
#     </ol>
#     <li><a href="#7">stride of feature convolution</a></li>
#     <li><a href="#8">لختی جمعیت نورونی لایه‌ی feature-maps</a></li>
#     <ol>
#         <li>کوچک‌تر</li>
#         <li>بزرگ‌تر</li>
#     </ol>
#     <li><a href="#9">lateral</a></li>
#     <li><a href="#10">k winners</a></li>
#     <li><a href="#11">اندازه گام آموزشی (learning rate)</a></li>
#     <ol>
#         <li>کوچک‌تر</li>
#         <li>بزرگ‌تر</li>
#         <li>نسبت ltp و ltd</li>
#     </ol>
#     <li><a href="#12">on-set time</a></li>
#     <li><a href="#13">تعداد ویژگی‌ها</a></li>
# </ol>
# </div>

# In[44]:


import warnings
warnings.filterwarnings("ignore")
import torch


# <a id='1'></a>
# <div dir='rtl'>
# <h2>1. دادگان</h2>
#     <br/>
#     در این آزمایش از بخشی از دادگان
#     caltech
#     استفاده خواهیم کرد و سعی داریم ویژگی‌هایی برای تصاویر مربوط به گربه‌های وحشی در این دادگان استخراج کنیم.
#     این مجموعه شامل ۶۹ تصویر از گربه‌های وحشی است که از همه آن‌ها استفاده خواهیم کرد. توجه کنید که زاویه تصویر برداری و فرم بدن یا صورت این گربه‌ها لزوما ثابت نیست و این کمی کار مدل را دشوار می‌کند. برای سادگی، تصاویر را بدون رنگ به مدل ورودی می‌دهیم. در ادامه، نیم‌نگاهی به چند تصویر از این دادگان خواهیم داشت.
# </div>

# In[45]:


import matplotlib.pyplot as plt
from cnsproject.monitors.plotter import Plotter
from PIL import Image
import numpy as np
import os

path = "phase10_data/cougar_face/"
plt.figure(figsize=(20,2))
p = Plotter([
    [f'{i}' for i in range(10)]
])
for i,f in enumerate(os.listdir(path)[:10]):
    im = Image.open(path+f)
    im = im.resize((100, 100))
    im = np.array(im.convert('L'))
    gr_im= Image.fromarray(im)
    p.imshow(f'{i}', gr_im)
p.show()


# <a id='2'></a>
# <div dir='rtl'>
# <h2>2. برپایی آزمایش</h2>
#     <br/>
#     در این بخش دو تابع مهم تعریف می‌کنیم.
# </div>

# <div dir='rtl'>
# تابع اول عهده‌دار ساخت شبکه‌ی صورت پروژه با پارامتر‌هایی که در ورودی برای آن مشخص می‌شوند است. توجه کنید که تمام پارامتر‌ها (تا جزئی‌ترین آن‌ها) قابل تنظیم است اما تنها پارامتر‌هایی را در ورودی این تابع قرار می‌دهیم که در این آزمایش قصد بررسی اثر آن‌ها را داریم. برای باقی پارامتر‌ها مقدار پیش‌فرض قرار می‌دهیم. برای پارامتر‌های تحت تغییر نیز مجموعه‌ای از مقادیر پیش‌فرض قرار داده شده است تا شروع ساده‌تری داشته باشیم.
# <br/>
#     در بخش کدگذاری تصویر، همواره اسپایک‌ها لحظه آخر را نادیده خواهیم گرفت تا از اثر کاهندگی این اسپایک‌ها در روند آموزشی جلوگیری شود، چرا که این اسپایک‌ها مربوط به بخش‌هایی فاقد اطلاعات تصویر هستند.
# </div>

# In[104]:


from cnsproject.network.network import Network
from cnsproject.network.network_wrapper import *
from cnsproject.network.neural_populations import LIFPopulation, KWinnerTakeAllPopulationProxy
from cnsproject.network.synapse_sets import LazySynapseSet
from cnsproject.network.axon_sets import SimpleAxonSet
from cnsproject.network.dendrite_sets import FilteringDendriteSet2D
from cnsproject.network.encoders import Time2FirstSpikeEncoder
from cnsproject.network.filters import Conv2DFilter
from cnsproject.network.kernels import DoG_kernel
from cnsproject.learning.learning_rule_enforcers import FlatKernelSTDP
from cnsproject.monitors.monitors import Monitor
from torchvision import transforms
from cnsproject.learning.learning_rates import stdp_wdlr
size=(120,120)

def build_net(features=6, time=10,
              feature_kernel_size=(29,29),
              DoG_kernel_size=15,
              feature_kernel_initialization=lambda shape: torch.rand(shape)/5+4/10,
              feature_conv_stride=1,
              lif_tau=50,
              lateral=(2,2),
              k_winners=2,
              ltp_wdlr=stdp_wdlr(0.1),
              ltd_wdlr=stdp_wdlr(0.03),
             ):
    net = Network(dt=1.)
    net += Time2FirstSpikeEncoder(
            'encoder',
            shape=size,
            time=time+1,
            filt=Conv2DFilter(
                kernel=DoG_kernel(
                    kernel_size=DoG_kernel_size
                ),
                stride=2,
                transform=transforms.Compose([
                    lambda x: torch.from_numpy(x) if type(x) is not torch.Tensor else x,
                    lambda x: x.float(),
                ]),
                post_reshape_transform=transforms.Normalize(.5,.5),
            ),
        )
    net += LazySynapseSet('conv')         |FROM| (SimpleAxonSet(scale=100) |OF| net['encoder'])         |TO| FilteringDendriteSet2D(
                filt=Conv2DFilter(
                    kernel=feature_kernel_initialization((features,1,*feature_kernel_size)),
                    channel_inputing=False,
                    stride=feature_conv_stride,
                    bias=False,
                )
            )
    net += KWinnerTakeAllPopulationProxy(
            population=LIFPopulation(
                'kWinner',
                net[[['conv']]].dendrite.required_population_shape(),
                tau=lif_tau,
            ),
            lateral=lateral,
            k=k_winners
        ) |USING| net[[['conv']]].dendrite
    net += FlatKernelSTDP(
            synapse=net[[['conv']]],
            ltp_wdlr=ltp_wdlr,
            ltd_wdlr=ltd_wdlr,
        )
    net.reset()
    return net


# <div dir='rtl'>
# تابع دوم مسئول اجرای طرح مسئله بر روی شبکه‌ای است که توسط تابع اول ساخته می‌شود. آزمایش به این صورت تعریف می‌شود که به تعدادی دفعات (مقدار پیش‌فرض ۳۰۰ است اما مقادیر دیگر نیز بررسی خواهند شد)، تصویر تصادفی از بین تصاویر موجود انتخاب خواهد شد و پس از پیش‌پردازش مقدماتی (gray کردن و تغییر ابعاد به مقدار پیش‌فرض 120x120)،
#     هر تصویر به مدت ۱۰ ثانیه در اختیار مدل قرار داده خواهد شد. این تابع در خروجی پلات‌هایی از ویژگی‌های آموزش دیده در مراحل مختلف ایجاد خواهد کرد.
# </div>

# In[105]:


def train(net, epochs=300, plots_count=11, time=10, features=6):
    plt.figure(figsize=(plots_count,features+2))
    p = Plotter([
        [f'im{e}' for e in range(plots_count)],
        [f'enc{e}' for e in range(plots_count)],
        *[
            [f'f{f}_{e}' for e in range(plots_count)]
            for f in range(features)
        ]
    ])
    plots_count -= 1
    for e in range(epochs+1):
        index = int(torch.rand(1)*len(os.listdir(path)))
        f = os.listdir(path)[index]
        im = Image.open(path+f)
        im = im.resize(size)
        im = np.array(im.convert('L'))
        net.reset()
        net['encoder'].encode(im)
        for i in range(time):
            net.run()
        print(f'\repoch: {e}/{epochs}',end='')
        if (e%(epochs//plots_count))!=0:
            continue
        e_num = e//(epochs//plots_count)
        gr_im= Image.fromarray(im)
        p.imshow(f'im{e_num}', gr_im, title=f'Epoch: {e}' if e_num==0 else str(e),
                 y_label='image' if e_num==0 else '')
        p.imshow(f'enc{e_num}', net['encoder'].stage, y_label='DoG output' if e_num==0 else '')
        for feature in range(features):
            p.imshow(f'f{feature}_{e_num}', net[[['conv']]].dendrite.filter.core.weight.data[feature,0],
                    y_label=f'feature{feature}' if e_num==0 else '')
    p.show()


# <div dir='rtl'>
# تابع زیر، حاصل تلفیق دو تابع قبل است و از این پس فقط از آن استفاده خواهد شد.
# </div>

# In[106]:


def simulate(epochs=300, plots_count=11, time=10, features=6, **args):
    train(
        build_net(time=time, features=features, **args),
        epochs=epochs, plots_count=plots_count, time=time, features=features
    )


# <a id='3'></a>
# <div dir='rtl'>
# <h2>3. اجرای آزمایش با مقادیر پیش‌فرض</h2>
#     <br/>
#     مقادیر پیش‌فرض در تعریف تابع سازنده شبکه موجود هستند. عملکرد شبکه با این پارامتر‌ها را امتحان می‌کنیم.
# </div>

# In[118]:


simulate()


# <div dir='rtl'>
# همانطور که مشاهده می‌کنیم، شبکه‌ی فوق در یافتن ویژگی‌ها موفق عمل کرده است. در پلات‌های رسم شده، می‌توان قالب‌هایی از استایل‌های مختلف صورت گربه وحشی را دید. در برخی از ویژگی‌ها تمرکز بر روی پوزه و در برخی دیگر تمرکز بر روی گوش‌ها می‌باشد. با توجه به اینکه اسکیل گربه‌ها در اکثر عکس‌ها نزدیک به هم بوده و اندازه کرنل نیز نسبتا بزرگ انتخاب شده، همه ویژگی‌ها سعی بر پیدا کردن الگوی همه‌ی صورت گربه داشته‌اند. با اینحال دیده می‌شود که هر ویژگی بر بخشی بیشتر از دیگری تمرکز داشته. به عنوان مثال، یکی فقط بر روی پوزه تمرکز کرده درحالی که دیگری تمرکز بیشتری بر چشم‌ها داشته. برخی نیز به یادگیری رنگ‌بندی و الگو‌های موجود در رنگ پوست موجود کرده‌اند.
# </div>

# <a id='4'></a>
# <div dir='rtl'>
# <h2>4. اندازه بزرگ کرنل ویژگی</h2>
#     <br/>
# </div>

# In[51]:


simulate(feature_kernel_size=(39,39))


# <div dir='rtl'>
# می‌بینیم که receptive field
# هر ویژگی بزرگ‌تر شده و این همان چیزی است که انتظار داشتیم. همچنین توجه کنید که حالا که ویژگی‌ها کلی‌تر نگاه می‌کنند، از جزئیات صورت عبور کرده و به استایل ایستادن حیوان نیز توجه کرده‌اند. به عنوان مثال می‌توان دید که در یک ویژگی، تصویر صورت حیوان به صورت نیم‌رخ است. همچنین در یک ویژگی، هاله‌ای از گردن حیوان نیز دیده می‌شود.
# </div>

# <a id='4'></a>
# <div dir='rtl'>
# <h2>4. اندازه کوچک کرنل ویژگی</h2>
#     <br/>
# </div>

# In[53]:


simulate(feature_kernel_size=(23,23))


# <div dir='rtl'>
# می‌بینیم که receptive field
# هر ویژگی کوچک‌تر شده و مدل به جزئیات وارد شده است. به عنوان مثال می‌بینیم که مدل مفصل به تشخیص پوزه حیوان پرداخته است. همچنین تمرکز زیادی بر روی نحوه اتصال بینی و چشمان حیوان داشته است. در نگاه اول بنظر می‌آید که مدل بخشی از ظرفیت خود را از دست داده و موفق به آموزش تعدادی از ویژگی‌ها نشده اما واقعیت آن است که این ویژگی‌ها به تشخیص نقش و نگار پوست حیوان اختصاص داده شده‌اند. توجه کنید که نقش پوس یک ویژگی رایج در تصاویر داده شده است.
# </div>

# <a id='5'></a>
# <div dir='rtl'>
# <h2>5. اندازه کوچک کرنل فیلتر DoG</h2>
#     <br/>
# </div>

# In[70]:


simulate(DoG_kernel_size=5)


# <div dir='rtl'>
# همانطور که در تصاویر خروجی فیلتر DoG مشاهده می‌کنیم،
#     این فیلتر وارد جزئیات شده و نقاط بیشتری را در خروجی خود قرار داده است.
#     این اثر باعث شده مدل نیز درگیر این جزئیات شود و مشاهده می‌کنیم که در ویژگی‌های آموزش داده شده،
#     درگیری مدل به جزئیات، یادگیری آن را خراب کرده و مدل الگو‌های مهم را پیدا نکرده است
#     (چون وجود جزئیات باعث کم شدن شباهت تصاویر و عدم توانایی مدل در تشخیص تکرار‌ها می‌شود).
# </div>

# <a id='6'></a>
# <div dir='rtl'>
# <h2>6. مقداردهی اولیه‌ی کرنل ویژگی‌ها</h2>
#     <br/>
#     در حالت پیشفرض، این مقداردهی به صورت تصادفی از اعداد بین 0.4 تا 0.6 انجام می‌شود.
#     دلیل این تصمیم آن است که ما از گام آموزشی (learning rate) وابسته به مقدار وزن‌ها استفاده می‌کنیم
#     و اگر مقدار اولیه‌ی وزن‌ها نزدیک به صفر یا یک باشد، یادگیری کند و یا حتی متوقف می‌شود. بنابراین برای یک شروع قوی‌تر، از این مقادیر استفاده کردیم. در ادامه، مقداردهی اولیه بدون این محدودیت را امتحان می‌کنیم که در این حالت، وزن‌ها به صورت تصادفی مقادیری در بازه‌ی صفر تا یک اتخاذ می‌کنند.
# </div>

# In[74]:


simulate(feature_kernel_initialization=lambda shape: torch.rand(shape))


# <div dir='rtl'>
# استدلالی که بالاتر آورده بودیم را در نتایج مشاهده می‌کنید. وزن‌های نهایی نتوانستند خیلی از مقادیر اولیه خود فاصله بگیرند.
# </div>

# <div dir='rtl'>
# توجه کنید که چون از سیاست‌های بازدارنده استفاده می‌کنیم، هم‌مقدار بودن وزن‌های اولیه‌ی همه ویژگی‌ها مشکل‌ساز نخواهد بود. اگر از سیاست‌های بازدارنده استفاده نمی‌کردیم، لازم داشتیم تا مقدار اولیه‌ی ویژگی‌ها مقادیر متفاوتی باشد تا به ویژگی‌های متمایزی همگرا شوند. این مسئله را در زیر بررسی کردیم و همانطور که مشاهده می‌کنید، مقدار ثابت 0.5 برای مقدار اولیه‌ی همه‌ی وزن‌ها درنظر گرفته شده و با این‌حال، یادگیری به شکل کامل انجام شده است. 
# </div>

# In[75]:


simulate(feature_kernel_initialization=lambda shape: torch.zeros(shape)+.5)


# <a id='7'></a>
# <div dir='rtl'>
# <h2>7. stride of feature convolution</h2>
#     <br/>
# از آنجایی که اندازه کرنل ویژگی بزرگ اتخاذ شده (مقدار ۲۹)، شاید افزایش stride لایه‌ی کانولوشن مربوط به ویژگی‌ها صدمه‌ی چندانی به کیفیت ویژگی‌ها نزند. فایده‌ی این کار کاهش لود مدل و افزایش سرعت و بهینه کردن فرآیند است.
# </div>

# In[82]:


simulate(feature_conv_stride=4)


# <div dir='rtl'>
# مشاهده می‌کنیم که کیفیت (رزولوشن) ویژگی‌های استخراج شده پایین آمده ولی با اینحال نماهای درستی از ویژگی‌ها ارائه می‌دهند. با اینحال به دلیل کیفیت پایین نمایش ویژگی‌ها، از این بهینگی صرف‌نظر می‌کنیم.
# </div>

# <a id='8'></a>
# <div dir='rtl'>
# <h2>8. لختی جمعیت نورونی لایه‌ی feature-maps</h2>
#     <br/>
# یکی از پارامتر‌های تاثیرگذار در این آزمایش، میزان لختی (tau) جمعی‌های نورونی feature-maps می‌باشد.
#     دلیل این امر به منطق یادگیری STDP مرتبط است. می‌دانیم که این یادگیری در حالتی که نورون‌های feature-maps اسپایک  زده باشند و حالا نورون‌های ورودی اسپایک بزنند، موجب کاهش وزن‌ها می‌شود.
#     همچنین با توجه به اینکه سیاست‌های بازدارنده‌ی ما باعث می‌شود نورون‌های feature-maps اسپایک‌های چندباره نزنند،
#     اسپایک زودهنگام نورون‌های feature-maps باعث افزایش تغییرات منفی وزن‌های کرنل‌ها می‌شود و یادگیری را محدود 
#     می‌کند (ویژگی‌ها به خلوتی گراییده می‌شوند). لختی نورون‌های این جمعیت‌ها
# می‌توانند با این مشکل مقابله کنند چرا که افزایش لختی این نورون‌ها باعث به تعویق انداختن اسپایک این نورون‌ها می‌شود و تعادل مورد بحث برقرار می‌شود. همچنین این لختی می‌تواند در جامع‌نگری مدل برای انواع روشنایی‌های موجود در یک تصویر مفید باشد.
# </div>

# <div dir='rtl'>
# انتظار داریم با کاهش میزان این لختی، شاهد ویژگی‌های تاریک‌تر باشیم که در زیر همین پدیده را مشاهده می‌کنیم.
# </div>

# In[87]:


simulate(lif_tau=15)


# <div dir='rtl'>
# همچنین عکس قضیه‌ی بالا برقرار است و با افزایش این میزان لختی، انتظار دیدن ویژگی‌های شلوغ‌تر داریم که در زیر، با همین پدیده روبرو هستیم.
# </div>

# In[88]:


simulate(lif_tau=100)


# <a id='9'></a>
# <div dir='rtl'>
# <h2>9. lateral</h2>
#     <br/>
# قبل از بررسی این ویژگی باید اشاره شود که پیاده‌سازی این ویژگی به صورت خاصی صورت گرفته که منطبق بر تدریس صورت گرفته نیست (البته که هماهنگ شده است). lateral inhibition در این پیاده سازی به شکلی صورت گرفته است که اسپایک نورون‌های اطراف را به تعویق نمی‌اندازد، بلکه آن را مسدود می‌کند.
#     <br/>
#     انتظار داریم با افزایش این پارامتر، ویژگی‌ها از هم فاصله بگیرند و به بخش‌های متفاوتی از تصویر دقت کنند.
# </div>

# In[92]:


simulate(lateral=(7,7))


# <div dir='rtl'>
# اثبات این اثر با توجه به خروجی‌ها کمی دشوار است اما با دقت زیاد می‌توان مشاهده کرد که نسبت به خروجی‌های مدل پیش‌فرض، ویژگی‌ها از نظر جایگاه تصویر حیوان، تمایز بیشتری دارند.
# </div>

# <a id='10'></a>
# <div dir='rtl'>
# <h2>10. k winners</h2>
#     <br/>
#     انتظار می‌رود افزایش این پارامتر موجب تسریع آموزش و افزایش شباهت بین ویژگی‌های آموزش دیده شده شود. دلیل این دو انتظار آن است که افزایش k به معنی افزایش میزان آموزش با مشاهده هر تصویر است و در عین حال، تعداد بیشتری از ویژگی‌ها با هر یک از تصاویر منطبق می‌شوند.
# </div>

# In[103]:


simulate(k_winners=6)


# <div dir='rtl'>
# دقیقا نتایج مورد انتظار مشاهده می‌شود. ویژگی‌ها به شدت به هم شبیه شده‌اند و می‌بینیم که از ایپاک‌های بین ۲۰۰ تا ۲۵۰، به نتایجی رسیدیم که پیشتر برای دستیابی به آن کیفیت حداقل ۳۰۰ ایپاک نیاز داشتیم.
# </div>

# <a id='11'></a>
# <div dir='rtl'>
# <h2>11. اندازه گام آموزشی (learning rate)</h2>
# </div>

# <div dir='rtl'>
# انتظار می‌رود با افزایش اندازه گام آموزشی، با یادگیری سریع‌تر روبرو شویم که جامع‌نگری کمتری دارد و نسبت به یکسری تصاویر بیش‌پردازش می‌شود. دلیل آن است که وقتی یادگیری سریع‌تر انجام می‌شود، مدل با دیدن هر تصویر، میزان زیادی از آموزش را انجام می‌دهد و با دیدن تصاویر کمتری به ثبات می‌رسد. نمودار‌های زیر همین نتیجه را به ما نشان می‌دهند.
# </div>

# In[107]:


simulate(
    ltp_wdlr=stdp_wdlr(0.3),
    ltd_wdlr=stdp_wdlr(0.09),
)


# <div dir='rtl'>
# با استدلالی مشابه، انتظار داریم با کاهش اندازه گام آموزشی، یادگیری کندتر و جامع‌بین‌تر شود که نتایج زیر نیز همین را به ما نشان می‌دهند.
# </div>

# In[109]:


simulate(
    ltp_wdlr=stdp_wdlr(0.05),
    ltd_wdlr=stdp_wdlr(0.015),
    epochs=500,
    plots_count=16
)


# <div dir='rtl'>
# نکته‌ی مهم دیگری که در اندازه گام‌های آموزشی مهم است، نسبت گام آموزشی اثرات منفی به اثرات مثبت است. با افزایش این نسبت، با شرایطی مشابه آنچه در بخش لختی نورون‌های feature-maps بیان شد روبرو می‌شویم و کاهش زیاد وزن‌ها باعث ایجاد ویژگی‌هایی بیش از حد خلوت می‌شود.
# </div>

# In[110]:


simulate(
    ltp_wdlr=stdp_wdlr(0.1),
    ltd_wdlr=stdp_wdlr(0.1),
)


# <a id='12'></a>
# <div dir='rtl'>
# <h2>12. on-set time</h2>
# </div>

# In[115]:


simulate(time=30)


# <div dir='rtl'>
# همانطور که مشاهده می‌کنیم، افزایش این پارامتر مانند کاهش لختی نورون‌های feature-maps است که پیشتر بررسی شد. این شباهت منطقی است چرا که همان اثر دوباره مشاهده می‌شود. با افزایش زمان مشاهده تصویر، میزان اثر ltd افزایش پیدا کرده و ویژگی‌ها را تاریک‌تر می‌کند.
# </div>

# <a id='13'></a>
# <div dir='rtl'>
# <h2>13. تعداد ویژگی‌ها</h2>
# </div>

# In[116]:


simulate(features=12)


# <div dir='rtl'>
# مشاهده می‌کنیم که با افزایش تعداد ویژگی‌ها، مدل به سراغ یافتن ویژگی‌هایی با اسکیل‌های متفاوت رفته و ویژگي‌ها با زوم‌های متفاوتی استخراج کرده است. این عمل مورد انتظار بوده چون وقتی تعداد ویژگی‌های بیشتری داشته باشد، می‌تواند تعدادی از آن‌ها را به تصاویری با زوم کم (یا زیاد) اختصاص دهد و آن‌ها را نیز بیاموزد با اینکه مکررترین تصاویر نیستند.
#     <br/>
#     <br/>
#     نکته پیاده‌سازی: توجه شود که چون ویژگی‌ها مستقل پیاده‌سازی نشده‌اند و یکی از ابعاد کرنل ویژگی‌ها را تشکیل می‌دهند، یادگیری تعداد ویژگی‌های بیشتر یادگیری را خیلی کند نمی‌کند و این خبری بسیار خوش‌آیند می‌باشد.
# </div>